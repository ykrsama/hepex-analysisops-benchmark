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
    spec_dir: str
    rubric_path: str = "rubric.yaml"
    judge_prompt_path: str = "judge_prompt.md"
    eval_ref_path: Optional[str] = "eval_ref.yaml"

    # (optional) for white agent request description
    description: Optional[str] = None
    constraints: dict[str, Any] = Field(default_factory=dict)

    def resolve_path(self, rel: str | None) -> Optional[Path]:
        if not rel:
            return None
        p = Path(self.spec_dir) / rel
        return p


class GreenConfig(BaseModel):
    data_dir: str = "/tmp/atlas_data_cache"
    task_dirs: list[str] = Field(default_factory=lambda: ["specs/zpeak_fit", "specs/hyy"])


def load_task_spec(spec_dir: str | Path) -> TaskSpec:
    spec_dir = str(spec_dir)
    path = Path(spec_dir) / "task_spec.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    # enforce spec_dir from directory (source of truth)
    data["spec_dir"] = spec_dir

    return TaskSpec.model_validate(data)
