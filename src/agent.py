from __future__ import annotations

import os
import shutil
from typing import Any, Optional

from pydantic import BaseModel, HttpUrl, ValidationError
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart, DataPart
from a2a.utils import get_message_text, new_agent_text_message

from messenger import Messenger
from tasks.task_spec import GreenConfig, TaskSpec

from utils import _utc_now_iso, _new_run_id, _safe_write_json, _safe_write_text
from utils.atlas_download import ensure_atlas_open_data_downloaded  # <-- 用底层 ensure
from engine.runner import run_engine_for_task
from utils.mock_traces import mock_trace_zpeak_fit, mock_trace_hyy
from dotenv import load_dotenv, find_dotenv
from pathlib import Path


class EvalRequest(BaseModel):
    participants: dict[str, HttpUrl]  # role -> agent URL
    config: dict[str, Any]


class Agent:
    required_roles: list[str] = []  # later: ["white_agent"]

    def __init__(self):
        load_dotenv(find_dotenv())
        self.messenger = Messenger()

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        missing_roles = set(self.required_roles) - set(request.participants.keys())
        if missing_roles:
            return False, f"Missing roles: {sorted(missing_roles)}"
        return True, "ok"

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

    def _task_output_dir(self, base_dir: str, task: TaskSpec) -> str:
        """
        Make per-task dirs deterministic to avoid collisions across tasks/configs.
        """
        # Include max_files so different truncations don't share partial caches.
        return os.path.join(
            base_dir,
            task.release,
            task.dataset,
            task.skim,
            f"max_files={task.max_files}",
        )
    
    def _runs_root(self, base_data_dir: str) -> Path:
        # runs 和 data 同级：如果你 base_data_dir 是 /tmp/atlas_data_cache
        # 那 runs 会是 /tmp/atlas_data_cache/runs
        return Path(base_data_dir) / "runs"

    def _task_run_dir(self, runs_root: Path, run_id: str, task_id: str) -> Path:
        return runs_root / run_id / task_id
    

    async def _get_submission_trace(
        self,
        task: TaskSpec,
        request: EvalRequest,
        data_info: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        mode = getattr(task, "mode", "mock")

        if mode == "mock":
            if task.type == "zpeak_fit":
                return mock_trace_zpeak_fit(task.id)
            if task.type == "hyy_analysis":
                return mock_trace_hyy(task.id)
            return {"task_id": task.id, "status": "error", "error": f"Unknown task type: {task.type}"}

        # Future: call white agent
        return {"task_id": task.id, "status": "error", "error": "call_white not implemented yet"}

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        input_text = get_message_text(message)

        # 1) Parse platform request
        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid request: {e}"))
            return

        # 2) Parse green config
        try:
            cfg = GreenConfig.model_validate(request.config)
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid config: {e}"))
            return

        base_data_dir = self._resolve_data_dir(cfg)

        run_id = _new_run_id()
        runs_root = self._runs_root(base_data_dir)
        runs_root.mkdir(parents=True, exist_ok=True)

        await updater.update_status(TaskState.working, new_agent_text_message("Starting tasks..."))

        overall: dict[str, Any] = {
            "run_id": run_id,                              # NEW
            "run_dir": str((runs_root / run_id).resolve()),# NEW
            "data_dir": os.path.abspath(base_data_dir),
            "tasks": [],
            "score_total": 0.0,                 # sum of normalized per task
            "score_max": float(len(cfg.tasks)), # maximum normalized sum
        }

        # 3) Run tasks sequentially
        for idx, task in enumerate(cfg.tasks, start=1):
            task_dir = self._task_run_dir(runs_root, run_id, task.id)  # NEW
            task_dir.mkdir(parents=True, exist_ok=True)                # NEW

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
            }
            _safe_write_json(task_dir / "meta.json", meta)

            await updater.update_status(
                TaskState.working,
                new_agent_text_message(f"Task {idx}/{len(cfg.tasks)}: {task.type} ({task.id})"),
            )

            # 3a) Ensure data (optional)
            data_info: Optional[dict[str, Any]] = None
            if getattr(task, "needs_data", False):
                task_dir = self._task_output_dir(base_data_dir, task)
                os.makedirs(task_dir, exist_ok=True)

                if data_info is not None:
                    _safe_write_json(task_dir / "data_info.json", data_info)


                if not getattr(task, "reuse_existing", True):
                    # Force a clean re-download for this task configuration
                    try:
                        shutil.rmtree(task_dir)
                    except FileNotFoundError:
                        pass
                    os.makedirs(task_dir, exist_ok=True)

                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(f"[{task.id}] Ensuring data in {task_dir} ..."),
                )

                try:
                    # NOTE: workers not in TaskSpec -> pick a sane default or read env
                    workers = int(os.getenv("HEPEX_DOWNLOAD_WORKERS", "6"))
                    data_info = ensure_atlas_open_data_downloaded(
                        skim=task.skim,
                        release=task.release,
                        dataset=task.dataset,
                        protocol=task.protocol,
                        output_dir=task_dir,
                        max_files=task.max_files or 0,
                        workers=workers,
                        verbose=True,
                    )
                except Exception as e:
                    task_report = {
                        "task_id": task.id,
                        "type": task.type,
                        "status": "error",
                        "error": f"Data download failed: {type(e).__name__}: {e}",
                        "final": {"total_score": 0.0, "max_score": 1.0, "normalized_score": 0.0},
                    }
                    overall["tasks"].append(task_report)

                    await updater.add_artifact(
                        parts=[
                            Part(root=TextPart(text=f"[{task.id}] ERROR: data download failed.")),
                            Part(root=DataPart(data=task_report)),
                        ],
                        name=f"Result-{task.id}",
                    )
                    continue

                n_ok = data_info.get("n_ok", data_info.get("n_files", 0))
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(f"[{task.id}] Data ready: {n_ok} files."),
                )

            # 3b) Get submission trace
            submission_trace = await self._get_submission_trace(task, request, data_info)
            _safe_write_json(task_dir / "submission_trace.json", submission_trace)


            # persist judge input snapshot (what engine sees)
            judge_input = {
                "task_spec": task.model_dump(),  # pydantic v2
                "data_info": data_info,
                "submission_trace": submission_trace,
            }
            _safe_write_json(task_dir / "judge_input.json", judge_input)

            # 3c) Evaluate
            try:
                report = run_engine_for_task(
                    task_spec=task,
                    data_info=data_info,
                    submission_trace=submission_trace,
                )
            except Exception as e:
                err_text = f"{type(e).__name__}: {e}"
                _safe_write_text(task_dir / "engine_error.txt", err_text)

                report = {
                    "task_id": task.id,
                    "type": task.type,
                    "status": "error",
                    "error": f"Engine failed: {err_text}",
                    "final": {"total_score": 0.0, "max_score": 1.0, "normalized_score": 0.0},
                }

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

            _safe_write_json(task_dir / "judge_output.json", report)

            # update meta with score
            meta.update({
                "score_total": total_score,
                "score_max": max_score,
                "normalized_score": normalized,
                "finished_at": _utc_now_iso(),
                "status": report.get("status", "ok"),
            })
            _safe_write_json(task_dir / "meta.json", meta)

            summary = f"[{task.id}] {task.type}: score={total_score:.2f}/{max_score:.2f} (norm={normalized:.3f})"
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
