from __future__ import annotations

import os
import shutil
from typing import Any, Optional
import json
import logging
import re

from pydantic import BaseModel, HttpUrl, ValidationError
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart, DataPart
from a2a.utils import get_message_text, new_agent_text_message

from messenger import Messenger
from tasks.task_spec import GreenConfig, TaskRuntimeOverride, TaskSpec, load_task_spec

from utils import _utc_now_iso, _new_run_id, _safe_write_json, _safe_write_text
from utils.atlas_download import ensure_atlas_open_data_downloaded  
from engine.package_loader import load_spec_bundle, load_solver_prompt, load_submission_contract, load_private_l1_rubric
from engine.prompt_render import _builtin_minimal_prompt
from engine.evaluator import evaluate_task
from engine.llm_judge import get_judge
from engine.contract_validator import validate_contract, validate_submission_dir
from engine.input_access import resolve_input_access, InputAccessError
from engine.submission_bundle import (
    SubmissionBundleError,
    parse_submission_bundle,
    materialize_submission_bundle,
)
from engine.secret_store import SecretStore, patched_env
from engine.l1_scorer import rubric_unavailable_report, score_submission

from utils.mock_traces import get_mock_bundle, get_mock_trace
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

try:
    from json_repair import repair_json as _json_repair
    _JSON_REPAIR_AVAILABLE = True
except ImportError:
    _JSON_REPAIR_AVAILABLE = False


logger = logging.getLogger(__name__)

class EvalRequest(BaseModel):
    participants: dict[str, HttpUrl]  # role -> agent URL
    config: dict[str, Any]


class Agent:
    required_roles: list[str] = []  # later: ["purple_agent"]

    def __init__(self):
        load_dotenv(find_dotenv())
        self.messenger = Messenger()
        try:
            self.llm_judge = get_judge()
        except RuntimeError as e:
            logger.warning(f"Judge initialization failed, evaluation requiring LLMs will fail: {e}")
            self.llm_judge = None

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        participant_keys = set(request.participants.keys())
        if "white_agent" in participant_keys:
            participant_keys.add("purple_agent")
        missing_roles = set(self.required_roles) - participant_keys
        if missing_roles:
            return False, f"Missing roles: {sorted(missing_roles)}"
        return True, "ok"

    @staticmethod
    def _resolve_purple_agent_url(request: EvalRequest) -> str:
        purple_url = request.participants.get("purple_agent")
        if purple_url is not None:
            return str(purple_url)
        legacy_white_url = request.participants.get("white_agent")
        if legacy_white_url is not None:
            return str(legacy_white_url)
        if len(request.participants) == 1:
            return str(next(iter(request.participants.values())))
        raise KeyError("Missing participant role: expected 'purple_agent' (or legacy 'white_agent').")

    @staticmethod
    def _persist_json_if_enabled(path: Path, payload: Any, enabled: bool) -> None:
        if enabled:
            _safe_write_json(path, payload)

    @staticmethod
    def _persist_text_if_enabled(path: Path, text: str, enabled: bool) -> None:
        if enabled:
            _safe_write_text(path, text)

    @staticmethod
    def _raw_response_metadata(response_str: str, *, path: Optional[str] = None) -> dict[str, Any]:
        preview = response_str[:1000]
        metadata: dict[str, Any] = {
            "raw_response_preview": preview,
            "raw_response_length": len(response_str),
        }
        if path:
            metadata["raw_response_path"] = path
        return metadata

    def _resolve_data_dir(self, cfg: GreenConfig) -> str:
        """
        Precedence:
        1) cfg.data_dir if non-empty
        2) env HEPEX_DATA_DIR if set
        3) fallback to cfg.data_dir default (already set)
        """
        env_dir = os.getenv("HEPEX_DATA_DIR")
        if getattr(cfg, "data_dir", "").strip():
            return cfg.data_dir
        if env_dir and env_dir.strip():
            return env_dir
        return cfg.data_dir  # default

    def _task_data_dir(self, base_dir: str, task: TaskSpec) -> Path:
        # input ROOT cache
        return Path(base_dir) / task.release / task.dataset / task.skim

    
    def _runs_root(self, base_data_dir: str) -> Path:
        return Path(base_data_dir) / "runs"

    @staticmethod
    def _has_runtime_shared_input(cfg: GreenConfig) -> bool:
        return bool(cfg.input_access_mode and cfg.shared_input_dir and cfg.input_manifest_path)

    def _build_mock_input_manifest(self, task: TaskSpec, task_eval_dir: Path) -> dict[str, Any]:
        shared_dir = task_eval_dir / "mock_shared_input"
        shared_dir.mkdir(parents=True, exist_ok=True)

        root_path = shared_dir / "events.root"
        if not root_path.exists():
            _safe_write_text(root_path, "placeholder")

        manifest_path = shared_dir / "input_manifest.json"
        manifest = {
            "task_id": task.id,
            "release": getattr(task, "release", None),
            "dataset": getattr(task, "dataset", None),
            "skim": getattr(task, "skim", None),
            "shared_input_dir": str(shared_dir),
            "input_manifest_path": str(manifest_path),
            "files": [
                {
                    "logical_name": root_path.name,
                    "path": str(root_path),
                    "size_bytes": root_path.stat().st_size,
                }
            ],
            "read_only_for_solver": True,
            "input_access_mode": "local_shared_mount",
            "synthetic_for_mock_mode": True,
        }
        _safe_write_json(manifest_path, manifest)
        return manifest

    def _task_eval_dir(self, runs_root: Path, run_id: str, task_id: str) -> Path:
        return runs_root / task_id

    @staticmethod
    def _extract_json_candidates(text: str) -> list[str]:
        """Return all top-level JSON object substrings found in text, in order.

        For each '{' that is at depth-0, attempt bracket-matching to a '}' and
        collect the candidate.  The last complete candidate is tried first by
        _parse_json_flexible because purple agents tend to emit a final
        authoritative JSON block after any explanatory prose.
        """
        candidates: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            if text[i] != "{":
                i += 1
                continue
            start = i
            depth = 0
            in_string = False
            escape = False
            j = start
            while j < n:
                ch = text[j]
                if escape:
                    escape = False
                    j += 1
                    continue
                if ch == "\\" and in_string:
                    escape = True
                    j += 1
                    continue
                if ch == '"':
                    in_string = not in_string
                    j += 1
                    continue
                if in_string:
                    j += 1
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(text[start : j + 1])
                        i = j + 1
                        break
                j += 1
            else:
                # Truncated at this start — keep the partial fragment and stop
                candidates.append(text[start:])
                break
            if not candidates or candidates[-1] != text[start:]:
                pass  # already advanced i
        return candidates

    @staticmethod
    def _extract_json_from_response(text: str) -> str:
        """Extract the best JSON object candidate from text.

        Priority:
        1. Markdown code block (```json ... ```)
        2. Last complete top-level JSON object (handles prose-before-JSON and
           prose-with-{}-before-JSON cases)
        3. Partial fragment from the last '{' when response is truncated
        """
        code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if code_block_match:
            return code_block_match.group(1).strip()

        candidates = Agent._extract_json_candidates(text)
        if not candidates:
            return text

        # Prefer the last candidate — purple agents typically emit the JSON last.
        # Return it for _parse_json_flexible to attempt json.loads / json_repair.
        return candidates[-1]

    @staticmethod
    def _parse_json_flexible(text: str) -> dict:
        """Parse JSON from a purple-agent response with graceful fallback for
        mixed-text, truncated, or mildly malformed payloads.

        Strategy:
        1. Find all top-level JSON object candidates in the text (handles prose
           before/after/interspersed with JSON).
        2. Try json.loads on each candidate, last-first (purple agents tend to
           emit the final authoritative JSON at the end).
        3. If all strict parses fail and json-repair is available, retry each
           candidate through repair, still last-first.
        4. Raise the original JSONDecodeError if everything fails.
        """
        # Code-block fast path
        code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if code_block_match:
            snippet = code_block_match.group(1).strip()
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                if _JSON_REPAIR_AVAILABLE:
                    try:
                        repaired = _json_repair(snippet, return_objects=True)
                        if isinstance(repaired, dict):
                            logger.warning("Purple agent code-block JSON required repair.")
                            return repaired
                    except Exception:
                        pass

        candidates = Agent._extract_json_candidates(text)
        if not candidates:
            candidates = [text]

        first_err: json.JSONDecodeError | None = None

        # Pass 1: strict parse, last candidate first
        for candidate in reversed(candidates):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e:
                if first_err is None:
                    first_err = e

        # Pass 2: json_repair fallback, last candidate first
        if _JSON_REPAIR_AVAILABLE:
            for candidate in reversed(candidates):
                try:
                    repaired = _json_repair(candidate, return_objects=True)
                    if isinstance(repaired, dict):
                        logger.warning(
                            "Purple agent response required JSON repair "
                            "(response may have been truncated or mixed with text). "
                            "Parsed data may be incomplete."
                        )
                        return repaired
                except Exception:
                    continue

        raise first_err or json.JSONDecodeError("No JSON found", text, 0)

    def _public_task_view(self, task: TaskSpec) -> dict[str, Any]:
        hidden = {
            "rubric_path",
            "eval_ref_path",
            "judge_prompt_path",
            "white_prompt_path",
        }
        return {k: v for k, v in task.model_dump().items() if k not in hidden}

    @staticmethod
    def _task_override_payload(override: TaskRuntimeOverride) -> dict[str, Any]:
        return override.model_dump(exclude_none=True)

    def _apply_task_runtime_override(
        self,
        task: TaskSpec,
        cfg: GreenConfig,
    ) -> tuple[Optional[TaskSpec], dict[str, Any]]:
        override = (cfg.task_overrides or {}).get(task.id)
        if override is None:
            return task, {}

        applied = self._task_override_payload(override)
        if applied.get("enabled") is False:
            return None, applied

        updates = {k: v for k, v in applied.items() if k != "enabled"}
        if not updates:
            return task, applied

        effective = TaskSpec.model_validate({**task.model_dump(), **updates})
        return effective, applied

    def _build_secret_backed_judge(self, secret_store: SecretStore):
        judge_env = secret_store.get_judge_env()
        if not judge_env:
            return self.llm_judge
        with patched_env(judge_env):
            try:
                return get_judge()
            except RuntimeError:
                return self.llm_judge

    def _validate_task_capabilities(self, task: TaskSpec, cfg: GreenConfig) -> None:
        if task.input_strategy == "shared_manifest":
            if not getattr(task, "needs_data", False):
                raise InputAccessError(
                    f"Task {task.id} uses input_strategy=shared_manifest but needs_data is false."
                )
            if not getattr(task, "requires_large_input_data", False):
                raise InputAccessError(
                    f"Task {task.id} uses input_strategy=shared_manifest but requires_large_input_data is false."
                )
            if not self._has_runtime_shared_input(cfg) and getattr(task, "mode", "mock") != "mock":
                raise InputAccessError(
                    f"Task {task.id} uses input_strategy=shared_manifest but runtime shared-input config is incomplete."
                )

        if task.solver_response_mode == "submission_bundle_v1" and not getattr(task, "submission_contract_path", None):
            raise SubmissionBundleError(
                f"Task {task.id} uses solver_response_mode=submission_bundle_v1 but has no submission_contract_path."
            )

        if task.evaluation_mode == "directory_contract_and_private_l1" and not getattr(task, "submission_contract_path", None):
            raise SubmissionBundleError(
                f"Task {task.id} uses evaluation_mode=directory_contract_and_private_l1 but has no submission_contract_path."
            )

    async def _prepare_task_input(
        self,
        task: TaskSpec,
        cfg: GreenConfig,
        base_data_dir: str,
        task_eval_dir: Path,
        updater: TaskUpdater,
    ) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]]]:
        self._validate_task_capabilities(task, cfg)

        if not getattr(task, "needs_data", False):
            return None, None

        if task.input_strategy == "shared_manifest":
            if self._has_runtime_shared_input(cfg):
                input_manifest = resolve_input_access(task, cfg)
            elif getattr(task, "mode", "mock") == "mock":
                input_manifest = self._build_mock_input_manifest(task, task_eval_dir)
            else:
                raise InputAccessError(
                    f"Task {task.id} uses input_strategy=shared_manifest but runtime shared-input config is incomplete."
                )
            data_info = {
                "shared_input_dir": input_manifest.get("shared_input_dir"),
                "input_manifest_path": input_manifest.get("input_manifest_path"),
                "n_files": len(input_manifest.get("files", [])),
            }
            _safe_write_json(task_eval_dir / "data_info.json", data_info)
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(f"[{task.id}] Shared input ready: {data_info['n_files']} files."),
            )
            return data_info, input_manifest

        if task.input_strategy != "download":
            raise InputAccessError(f"Unsupported input_strategy for task {task.id}: {task.input_strategy}")

        data_info = {
            "release": task.release,
            "dataset": task.dataset,
            "skim": task.skim,
            "protocol": task.protocol,
            "max_files": task.max_files,
            "download_managed_by": "solver",
        }
        _safe_write_json(task_eval_dir / "data_info.json", data_info)
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(
                f"[{task.id}] Delegating data download to solver: "
                f"{task.release}/{task.dataset}/{task.skim} (max_files={task.max_files})."
            ),
        )
        return data_info, None

    async def _collect_solver_output(
        self,
        task: TaskSpec,
        request: EvalRequest,
        task_eval_dir: Path,
        data_info: Optional[dict[str, Any]],
        input_manifest: Optional[dict[str, Any]],
        persist_payloads: bool,
    ) -> dict[str, Any]:
        if task.solver_response_mode == "submission_trace":
            try:
                submission_trace = await self._get_submission_trace(
                    task,
                    request,
                    data_info,
                    task_eval_dir=task_eval_dir,
                    persist_payloads=persist_payloads,
                )
            except Exception as e:
                submission_trace = {
                    "task_id": task.id,
                    "status": "error",
                    "error": f"Failed to get submission trace: {type(e).__name__}: {e}",
                }
            _safe_write_json(task_eval_dir / "submission_trace.json", submission_trace)
            return {"submission_trace": submission_trace}

        if task.solver_response_mode == "submission_bundle_v1":
            contract = load_submission_contract(task)
            try:
                raw_bundle = await self._get_submission_bundle(
                    task,
                    request,
                    input_manifest or {},
                    task_eval_dir=task_eval_dir,
                    persist_payloads=persist_payloads,
                )
                self._persist_json_if_enabled(task_eval_dir / "submission_bundle_raw.json", raw_bundle, persist_payloads)
                parsed_bundle = parse_submission_bundle(raw_bundle, contract)
                artifact_manifest = materialize_submission_bundle(parsed_bundle, contract, task_eval_dir)
                submission_trace = json.loads((task_eval_dir / "submission_trace.json").read_text(encoding="utf-8"))
                self._persist_json_if_enabled(task_eval_dir / "artifact_manifest.json", artifact_manifest, persist_payloads)
                return {
                    "submission_trace": submission_trace,
                    "artifact_manifest": artifact_manifest,
                    "submission_bundle_raw": raw_bundle,
                }
            except Exception as e:
                submission_trace = {
                    "task_id": task.id,
                    "status": "error",
                    "error": f"Failed to get submission bundle: {type(e).__name__}: {e}",
                }
                if isinstance(e, SubmissionBundleError) and getattr(e, "raw_response", None):
                    submission_trace.update(
                        self._raw_response_metadata(
                            e.raw_response,
                            path="purple_response_raw.txt" if persist_payloads else None,
                        )
                    )
                _safe_write_json(task_eval_dir / "submission_trace.json", submission_trace)
                return {"submission_trace": submission_trace}

        raise SubmissionBundleError(
            f"Unsupported solver_response_mode for task {task.id}: {task.solver_response_mode}"
        )

    def _evaluate_submission(
        self,
        task: TaskSpec,
        task_eval_dir: Path,
        submission_trace: dict[str, Any],
        data_info: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        if task.evaluation_mode == "directory_contract_and_private_l1":
            contract_report = validate_submission_dir(task, task_eval_dir)
            if contract_report.get("status") != "ok":
                return contract_report

            secret_store = SecretStore()
            private_rubric = load_private_l1_rubric(task, secret_store)
            if private_rubric:
                return score_submission(
                    task,
                    task_eval_dir,
                    private_rubric,
                    contract_report,
                    judge=self._build_secret_backed_judge(secret_store),
                )
            return rubric_unavailable_report(
                task,
                contract_report,
                reason=(
                    "Task requires private-rubric scoring, but no matching private rubric was "
                    "available from GREEN_SECRETS_JSON."
                ),
            )

        if task.evaluation_mode != "legacy_trace_contract":
            raise RuntimeError(f"Unsupported evaluation_mode for task {task.id}: {task.evaluation_mode}")

        bundle = load_spec_bundle(task)  # {rubric, eval_ref, judge_prompt, ...}
        eval_ref = bundle.get("eval_ref", {}) or {}

        if bundle["rubric"]:
            spec = {
                "task": task.model_dump(),
                "rubric": bundle["rubric"],
                "eval_ref": eval_ref,
                "judge_prompt": bundle.get("judge_prompt"),
            }
            judge = self.llm_judge if (spec["rubric"].get("llm_checks") and spec.get("judge_prompt")) else None
            return evaluate_task(
                spec=spec,
                trace=submission_trace,
                judge=judge,
            )
        return validate_contract(task, submission_trace)

    async def _get_submission_trace(
        self,
        task: TaskSpec,
        request: EvalRequest,
        data_info: Optional[dict[str, Any]],
        *,
        task_eval_dir: Optional[Path] = None,
        persist_payloads: bool = True,
    ) -> dict[str, Any]:
        mode = getattr(task, "mode", "mock")

        if mode == "mock":
            return get_mock_trace(task.type, task.id)

        # Future: call purple agent
        # return {"task_id": task.id, "status": "error", "error": "call_white not implemented yet"}

        # ---- call_white path ----
        # V2: use load_solver_prompt() which resolves solver_prompt.md first,
        # then falls back to white_prompt.md (V1 compat).
        prompt = load_solver_prompt(task) or _builtin_minimal_prompt(task.id, task.type)

        # optional: simple templating
        prompt = (
            prompt
            .replace("{{TASK_ID}}", task.id)
            .replace("{{MAX_FILES}}", str(task.max_files))
        )

        # 2) prepare data payload
        files = []
        if data_info:
            # adapt this key if needed
            files = data_info.get("local_paths", [])

        payload = {
            "role": "task_request",
            "task_id": task.id,
            "task_type": task.type,
            "mode": mode,
            "prompt": prompt,
            "data": {
                "files": files[: task.max_files],
                "release": task.release,
                "dataset": task.dataset,
                "skim": task.skim,
                "protocol": task.protocol,
                "max_files": task.max_files,
                "input_strategy": task.input_strategy,
            },
            "constraints": getattr(task, "constraints", {}),
        }

        message_str = json.dumps(payload, indent=2)
        if task_eval_dir is not None:
            self._persist_json_if_enabled(task_eval_dir / "purple_request.json", payload, persist_payloads)

        # 3) send to purple agent
        purple_url = self._resolve_purple_agent_url(request)

        response_str = await self.messenger.talk_to_agent(
            message=message_str,
            url=purple_url,
            new_conversation=True,   # IMPORTANT: new task = new conversation
        )
        if task_eval_dir is not None:
            self._persist_text_if_enabled(task_eval_dir / "purple_response_raw.txt", response_str, persist_payloads)

        # 4) parse response - handle markdown fences, truncated, and repaired JSON
        try:
            submission_trace = self._parse_json_flexible(response_str)
        except json.JSONDecodeError as e:
            error_payload = {
                "task_id": task.id,
                "status": "error",
                "error": f"Purple agent returned non-JSON response: {e}",
            }
            error_payload.update(
                self._raw_response_metadata(
                    response_str,
                    path="purple_response_raw.txt" if persist_payloads else None,
                )
            )
            return error_payload

        return submission_trace

    async def _get_submission_bundle(
        self,
        task: TaskSpec,
        request: EvalRequest,
        input_manifest: dict[str, Any],
        *,
        task_eval_dir: Optional[Path] = None,
        persist_payloads: bool = True,
    ) -> dict[str, Any]:
        mode = getattr(task, "mode", "mock")
        if mode == "mock":
            bundle = get_mock_bundle(task.type, task.id)
            if bundle.get("status") == "error":
                raise SubmissionBundleError(bundle.get("error", f"Unknown mock bundle error for task {task.id}"))
            return bundle

        contract = load_submission_contract(task)
        prompt = load_solver_prompt(task) or _builtin_minimal_prompt(task.id, task.type)
        prompt = prompt.replace("{{TASK_ID}}", task.id).replace("{{MAX_FILES}}", str(task.max_files))

        payload = {
            "role": "task_request",
            "task_id": task.id,
            "task_type": task.type,
            "mode": mode,
            "level": getattr(task, "level", None),
            "prompt": prompt,
            "submission_contract": contract,
            "data": {
                "release": task.release,
                "dataset": task.dataset,
                "skim": task.skim,
                "protocol": task.protocol,
                "max_files": task.max_files,
                "input_strategy": task.input_strategy,
                "shared_input_dir": input_manifest.get("shared_input_dir"),
                "input_manifest_path": input_manifest.get("input_manifest_path"),
                "read_only_for_solver": True,
            },
            "constraints": {
                **(getattr(task, "constraints", {}) or {}),
                "response_format": "submission_bundle_v1",
                "allow_purple_network": False,
            },
        }
        if task_eval_dir is not None:
            self._persist_json_if_enabled(task_eval_dir / "purple_request.json", payload, persist_payloads)
        purple_url = self._resolve_purple_agent_url(request)
        response_str = await self.messenger.talk_to_agent(
            message=json.dumps(payload, indent=2),
            url=purple_url,
            new_conversation=True,
        )
        if task_eval_dir is not None:
            self._persist_text_if_enabled(task_eval_dir / "purple_response_raw.txt", response_str, persist_payloads)
        try:
            return self._parse_json_flexible(response_str)
        except json.JSONDecodeError as e:
            error = SubmissionBundleError(f"Purple agent returned non-JSON response: {e}")
            error.raw_response = response_str
            raise error from e


    async def run(self, message: Message, updater: TaskUpdater) -> None:
        input_text = get_message_text(message)

        # 1) Parse platform request
        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            # update, show received request
            logger.info(f"Received request: {request}")
            await updater.update_status(TaskState.working, new_agent_text_message(f"Received request: {request}"))
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid request: {e}"))
            return

        # 2) Parse green config
        try:
            cfg = GreenConfig.model_validate(request.config)
            # update, show received config
            logger.info(f"Received config: {cfg}")
            await updater.update_status(TaskState.working, new_agent_text_message(f"Received config: {cfg}"))
            
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid config: {e}"))
            return

        base_data_dir = self._resolve_data_dir(cfg)

        run_id = _new_run_id()
        runs_root = self._runs_root(base_data_dir)
        runs_root.mkdir(parents=True, exist_ok=True)

        await updater.update_status(TaskState.working, new_agent_text_message("Starting tasks..."))

        task_runs: list[tuple[TaskSpec, dict[str, Any]]] = []
        for task_dir in cfg.task_dirs:
            loaded = load_task_spec(task_dir)
            effective_task, applied_overrides = self._apply_task_runtime_override(loaded, cfg)
            if effective_task is None:
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(f"[{loaded.id}] Skipped by config.task_overrides."),
                )
                logger.info(f"Skipping task {loaded.id} due to runtime override: {applied_overrides}")
                continue
            task_runs.append((effective_task, applied_overrides))

        overall: dict[str, Any] = {
            "run_id": run_id,                              
            "run_dir": str(runs_root.resolve()),
            "data_dir": os.path.abspath(base_data_dir),
            "tasks": [],
            "score_total": 0.0,                 # sum of normalized per task
            "score_max": float(len(task_runs)), # maximum normalized sum
        }
        self._persist_json_if_enabled(runs_root / "eval_request.json", request.model_dump(mode="json"), cfg.persist_payloads)
        self._persist_json_if_enabled(runs_root / "green_config.json", cfg.model_dump(mode="json"), cfg.persist_payloads)

        # 3) Run tasks sequentially
        for idx, (task, applied_overrides) in enumerate(task_runs, start=1):
            task_eval_dir = self._task_eval_dir(runs_root, run_id, task.id)  
            task_eval_dir.mkdir(parents=True, exist_ok=True)                

            # NEW: meta skeleton (write early so crash still leaves trace)
            meta = {
                "timestamp": _utc_now_iso(),
                "task_id": task.id,
                "task_type": task.type,
                "mode": getattr(task, "mode", "mock"),
                "release": getattr(task, "release", None),
                "dataset": getattr(task, "dataset", None),
                "skim": getattr(task, "skim", None),
                "protocol": getattr(task, "protocol", None),
                "max_files": getattr(task, "max_files", None),
                "reuse_existing": getattr(task, "reuse_existing", None),
                "task_overrides_applied": applied_overrides,
            }
            _safe_write_json(task_eval_dir / "meta.json", meta)

            await updater.update_status(
                TaskState.working,
                new_agent_text_message(f"Task {idx}/{len(task_runs)}: {task.type} ({task.id})"),
            )
            logger.info(f"Starting Task {idx}/{len(task_runs)}: {task.type} ({task.id})")

            # 3a) Resolve data access
            data_info: Optional[dict[str, Any]] = None
            input_manifest: Optional[dict[str, Any]] = None
            try:
                data_info, input_manifest = await self._prepare_task_input(
                    task,
                    cfg,
                    base_data_dir,
                    task_eval_dir,
                    updater,
                )
            except (InputAccessError, SubmissionBundleError) as e:
                task_report = {
                    "task_id": task.id,
                    "type": task.type,
                    "status": "error",
                    "error": str(e),
                    "task_overrides_applied": applied_overrides,
                    "final": {"total_score": 0.0, "max_score": 1.0, "normalized_score": 0.0},
                }
                overall["tasks"].append(task_report)
                await updater.add_artifact(
                    parts=[
                        Part(root=TextPart(text=f"[{task.id}] ERROR: {e}")),
                        Part(root=DataPart(data=task_report)),
                    ],
                    name=f"Result-{task.id}",
                )
                continue
            except Exception as e:
                task_report = {
                    "task_id": task.id,
                    "type": task.type,
                    "status": "error",
                    "error": f"Data preparation failed: {type(e).__name__}: {e}",
                    "task_overrides_applied": applied_overrides,
                    "final": {"total_score": 0.0, "max_score": 1.0, "normalized_score": 0.0},
                }
                overall["tasks"].append(task_report)
                await updater.add_artifact(
                    parts=[
                        Part(root=TextPart(text=f"[{task.id}] ERROR: data preparation failed.")),
                        Part(root=DataPart(data=task_report)),
                    ],
                    name=f"Result-{task.id}",
                )
                continue

            # 3b) Get solver outputs
            collected = await self._collect_solver_output(
                task,
                request,
                task_eval_dir,
                data_info,
                input_manifest,
                cfg.persist_payloads,
            )
            submission_trace = collected["submission_trace"]


            # persist judge input snapshot (what engine sees)
            # Sensitive eval fields are stripped so this file is safe to write
            # in a public-facing run directory.
            judge_input = {
                "task_spec": self._public_task_view(task),
                "data_info": data_info,
                "submission_trace": submission_trace
                if task.solver_response_mode == "submission_trace"
                else {"path": "submission_trace.json"},
            }
            _safe_write_json(task_eval_dir / "judge_input.json", judge_input)

            # 3c) Evaluate
            try:
                report = self._evaluate_submission(
                    task,
                    task_eval_dir,
                    submission_trace,
                    data_info,
                )

            except Exception as e:
                err_text = f"{type(e).__name__}: {e}"
                _safe_write_text(task_eval_dir / "engine_error.txt", err_text)

                report = {
                    "task_id": task.id,
                    "type": task.type,
                    "status": "error",
                    "error": f"Engine failed: {err_text}",
                    "task_overrides_applied": applied_overrides,
                    "final": {"total_score": 0.0, "max_score": 1.0, "normalized_score": 0.0},
                }

            # Ensure task_id and type are always in the report
            report["task_id"] = task.id
            report["type"] = task.type
            report["task_overrides_applied"] = applied_overrides

            # 3d) Normalize and accumulate
            final = report.setdefault("final", {})
            total_score = float(final.get("total_score", 0.0))
            max_score = float(final.get("max_score", 100.0))
            denom = max(1e-9, max_score)
            normalized = total_score / denom

            final["total_score"] = total_score
            final["max_score"] = max_score
            final["normalized_score"] = normalized

            overall["score_total"] += normalized
            overall["tasks"].append(report)

            _safe_write_json(task_eval_dir / "judge_output.json", report)

            # update meta with score
            meta.update({
                "score_total": total_score,
                "score_max": max_score,
                "normalized_score": normalized,
                "finished_at": _utc_now_iso(),
                "status": report.get("status", "ok"),
            })
            _safe_write_json(task_eval_dir / "meta.json", meta)

            summary = f"[{task.id}] {task.type}: score={total_score:.2f}/{max_score:.2f} (norm={normalized:.3f})"
            logger.info(summary)
            await updater.add_artifact(
                parts=[Part(root=TextPart(text=summary)), Part(root=DataPart(data=report))],
                name=f"Result-{task.id}",
            )

        # 4) Summary
        done_text = (
            f"Done. Normalized score: {overall['score_total']:.3f}/{overall['score_max']:.3f}\n"
            f"run_id={overall['run_id']}\n"
            f"run_dir={overall['run_dir']}"
        )

        await updater.add_artifact(
            parts=[Part(root=TextPart(text=done_text)), Part(root=DataPart(data=overall))],
            name="Summary",
        )

        # 5) Complete (if supported)
        try:
            await updater.complete(new_agent_text_message(done_text))
        except Exception:
            await updater.update_status(TaskState.working, new_agent_text_message(done_text))
