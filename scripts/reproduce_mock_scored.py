#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml
from a2a.utils import new_agent_text_message

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent import Agent
from engine.package_loader import load_submission_contract
from engine.secret_store import SecretStore
from tasks.task_spec import load_task_spec
from utils.mock_private_rubrics import hyy_l1_private_rubric


DEFAULT_TASK_DIR = "tasks_public/t002_hyy_v5_l1"
DEFAULT_OUTPUT_DIR = "output"


class DummyUpdater:
    def __init__(self):
        self.status_updates: list[tuple[Any, Any]] = []
        self.artifacts: list[tuple[str, Any]] = []
        self.rejected = None
        self.completed = None

    async def update_status(self, state, message):
        self.status_updates.append((state, message))

    async def add_artifact(self, parts, name):
        self.artifacts.append((name, parts))

    async def reject(self, message):
        self.rejected = message

    async def complete(self, message):
        self.completed = message


def sample_private_rubric() -> dict[str, Any]:
    return hyy_l1_private_rubric()


def make_secret_store_payload(task_spec) -> str:
    contract = load_submission_contract(task_spec)
    contract_hash = SecretStore("").contract_hash(contract)
    rubric_b64 = base64.b64encode(
        yaml.safe_dump(sample_private_rubric(), sort_keys=False).encode("utf-8")
    ).decode("utf-8")
    return json.dumps(
        {
            "schema_version": 1,
            "tasks": {
                task_spec.id: {
                    "public_contract_sha256": contract_hash,
                    "private_rubric_yaml_b64": rubric_b64,
                }
            },
            "judge_env": {},
        }
    )


def _load_task_metadata(task_dir: Path) -> tuple[str, str, str]:
    task_spec_path = task_dir / "task_spec.yaml"
    task_spec = yaml.safe_load(task_spec_path.read_text(encoding="utf-8")) or {}
    release = task_spec.get("release")
    dataset = task_spec.get("dataset")
    skim = task_spec.get("skim")
    if not release or not dataset or not skim:
        raise ValueError(
            f"Task spec {task_spec_path} must define release, dataset, and skim for local shared-input runs."
        )
    return str(release), str(dataset), str(skim)


def prepare_mock_task(source_task_dir: Path, output_dir: Path) -> Path:
    mock_task_dir = output_dir / ".tmp" / "mock_tasks" / source_task_dir.name
    if mock_task_dir.exists():
        shutil.rmtree(mock_task_dir)
    shutil.copytree(source_task_dir, mock_task_dir)

    task_spec_path = mock_task_dir / "task_spec.yaml"
    task_spec = yaml.safe_load(task_spec_path.read_text(encoding="utf-8")) or {}
    task_spec["mode"] = "mock"
    task_spec_path.write_text(yaml.safe_dump(task_spec, sort_keys=False), encoding="utf-8")
    return mock_task_dir


def ensure_shared_input(task_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    release, dataset, skim = _load_task_metadata(task_dir)
    shared_dir = output_dir / "shared_input" / release / dataset / skim
    shared_dir.mkdir(parents=True, exist_ok=True)

    placeholder = shared_dir / "events.root"
    if not placeholder.exists():
        placeholder.write_text("placeholder", encoding="utf-8")

    manifest_path = shared_dir / "input_manifest.json"
    return shared_dir, manifest_path


async def run_mock_scored(task_dir: Path, output_dir: Path, persist_payloads: bool) -> tuple[Path, Path]:
    mock_task_dir = prepare_mock_task(task_dir, output_dir)
    shared_input_dir, input_manifest_path = ensure_shared_input(mock_task_dir, output_dir)

    task = load_task_spec(mock_task_dir)
    os.environ["GREEN_SECRETS_JSON"] = make_secret_store_payload(task)

    req = {
        "participants": {},
        "config": {
            "task_dirs": [str(mock_task_dir)],
            "data_dir": str(output_dir),
            "input_access_mode": "local_shared_mount",
            "shared_input_dir": str(shared_input_dir),
            "input_manifest_path": str(input_manifest_path),
            "allow_green_download": False,
            "persist_payloads": persist_payloads,
        },
    }

    updater = DummyUpdater()
    agent = Agent()
    agent._build_secret_backed_judge = lambda secret_store: None
    await agent.run(new_agent_text_message(json.dumps(req)), updater)

    if updater.rejected:
        raise RuntimeError(f"Green agent rejected request: {updater.rejected}")

    runs_root = output_dir / "runs"
    run_dirs = sorted([path for path in runs_root.iterdir() if path.is_dir()])
    if not run_dirs:
        raise RuntimeError(f"No run directories found in {runs_root}")

    run_dir = run_dirs[-1]
    task_dir = run_dir / task.id
    if not task_dir.exists():
        raise RuntimeError(f"Expected task directory not found: {task_dir}")
    return run_dir, task_dir


def main():
    parser = argparse.ArgumentParser(
        description="Run the Hyy L1 green-agent scoring path locally in mock mode and write results to output/runs."
    )
    parser.add_argument("--task-dir", default=DEFAULT_TASK_DIR, help="Source task directory to clone and patch to mock mode.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory that will receive runs/ and shared_input/.")
    parser.add_argument(
        "--no-persist-payloads",
        action="store_true",
        help="Do not persist eval/purple payload snapshots into the run directory.",
    )
    args = parser.parse_args()

    task_dir = (REPO_ROOT / args.task_dir).resolve()
    output_dir = (REPO_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not task_dir.exists():
        raise SystemExit(f"Task directory not found: {task_dir}")

    run_dir, scored_task_dir = asyncio.run(
        run_mock_scored(
            task_dir=task_dir,
            output_dir=output_dir,
            persist_payloads=not args.no_persist_payloads,
        )
    )

    judge_output = scored_task_dir / "judge_output.json"
    report = json.loads(judge_output.read_text(encoding="utf-8"))

    print("Mock scored run completed.")
    print(f"run_dir={run_dir}")
    print(f"task_dir={scored_task_dir}")
    print(f"judge_output={judge_output}")
    print(f"status={report.get('status')}")
    print(f"final={json.dumps(report.get('final', {}), ensure_ascii=False)}")
    print(f"dimension_scores={json.dumps(report.get('dimension_scores', {}), ensure_ascii=False)}")


if __name__ == "__main__":
    main()
