from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    # identity
    id: str
    type: str
    mode: Literal["mock", "call_white"] = "mock"

    # execution/data requirements
    needs_data: bool = True
    release: str = "2025e-13tev-beta"
    dataset: str = "data"
    skim: str
    protocol: str = "https"
    max_files: int = 3
    cache: bool = True
    reuse_existing: bool = True

    # evaluation specs (relative to spec_dir by default)
    # NOTE: spec_dir is only used for V1 specs/ layout; V2 tasks_public/ tasks omit it.
    spec_dir: Optional[str] = None

    # --- Transitional compatibility fields ---
    # These fields exist only for backward-compat with V1 specs/ layout.
    # They should be removed in a later cleanup phase once private eval is
    # fully decoupled from the public task contract.
    rubric_path: Optional[str] = None
    judge_prompt_path: Optional[str] = None
    eval_ref_path: Optional[str] = None
    white_prompt_path: Optional[str] = None  # V1 alias; prefer solver_prompt_path

    # V2 public contract: solver prompt path
    solver_prompt_path: Optional[str] = "solver_prompt.md"
    submission_contract_path: Optional[str] = "submission_contract.yaml"

    # (optional) task description & constraints
    description: Optional[str] = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    level: Optional[str] = None

    # Capability-driven execution routing
    input_strategy: Literal["download", "shared_manifest"] = "download"
    solver_response_mode: Literal["submission_trace", "submission_bundle_v1"] = "submission_trace"
    evaluation_mode: Literal["legacy_trace_contract", "directory_contract_and_private_l1"] = "legacy_trace_contract"

    # Task capabilities and defaults for large-input tasks.
    requires_large_input_data: bool = False
    supports_scenario_shared_input: bool = False
    supports_local_shared_input: bool = False

    def resolve_path(self, rel: str | None) -> Optional[Path]:
        if not rel:
            return None
        if self.spec_dir is None:
            return None
        p = Path(self.spec_dir) / rel
        return p


class TaskRuntimeOverride(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[Literal["mock", "call_white"]] = None
    input_strategy: Optional[Literal["download", "shared_manifest"]] = None
    max_files: Optional[int] = None
    reuse_existing: Optional[bool] = None
    cache: Optional[bool] = None
    release: Optional[str] = None
    dataset: Optional[str] = None
    skim: Optional[str] = None


class GreenConfig(BaseModel):
    data_dir: str = "/tmp/atlas_data_cache"
    # V2: task directories live under tasks_public/ with numeric prefix.
    # V1 specs/ paths still accepted for backward compatibility.
    task_dirs: list[str] = Field(default_factory=lambda: ["tasks_public/t001_zpeak_fit"])
    input_access_mode: Optional[Literal["scenario_shared_mount", "local_shared_mount"]] = None
    shared_input_dir: Optional[str] = None
    input_manifest_path: Optional[str] = None
    allow_green_download: bool = False
    persist_payloads: bool = True
    task_overrides: dict[str, TaskRuntimeOverride] = Field(default_factory=dict)


def load_task_spec(spec_dir: str | Path) -> TaskSpec:
    spec_dir = str(spec_dir)
    path = Path(spec_dir) / "task_spec.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    # Inject spec_dir so package_loader can resolve relative paths (V1 compat)
    data.setdefault("spec_dir", spec_dir)

    return TaskSpec.model_validate(data)
