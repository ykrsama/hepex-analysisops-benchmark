# src/engine/package_loader.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, TypedDict

import yaml


class SpecBundle(TypedDict):
    rubric: Dict[str, Any]
    eval_ref: Dict[str, Any]
    judge_prompt: Optional[str]   # None if not needed
    white_prompt: Optional[str]   # None if missing


def _read_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _resolve_path(spec_dir: str | Path, maybe_path: str) -> Path:
    p = Path(maybe_path)
    if p.is_absolute():
        return p
    return Path(spec_dir) / p


def _has_llm_checks(rubric: Dict[str, Any]) -> bool:
    llm_checks = rubric.get("llm_checks", None)
    return isinstance(llm_checks, list) and len(llm_checks) > 0


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from object, supporting both Pydantic models and dicts."""
    val = getattr(obj, key, None)
    if val is not None:
        return val
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def load_spec_bundle(task: Any) -> SpecBundle:
    spec_dir = _safe_get(task, "spec_dir")
    if spec_dir is None:
        raise ValueError("task must have 'spec_dir' attribute")

    rubric_rel = _safe_get(task, "rubric_path", "rubric.yaml")
    prompt_rel = _safe_get(task, "judge_prompt_path", "judge_prompt.md")
    eval_ref_rel = _safe_get(task, "eval_ref_path", "eval_ref.yaml")
    white_prompt_rel = _safe_get(task, "white_prompt_path", "white_prompt.md")

    # rubric required
    rubric_path = _resolve_path(spec_dir, rubric_rel)
    if not rubric_path.exists():
        raise FileNotFoundError(f"rubric not found: {rubric_path}")
    rubric = _read_yaml(rubric_path)

    # eval_ref optional
    eval_ref: Dict[str, Any] = {}
    if eval_ref_rel:
        p = _resolve_path(spec_dir, eval_ref_rel)
        if p.exists():
            eval_ref = _read_yaml(p)

    # judge_prompt only if llm_checks exist
    judge_prompt: Optional[str] = None
    if _has_llm_checks(rubric):
        p = _resolve_path(spec_dir, prompt_rel)
        if not p.exists():
            raise FileNotFoundError(f"rubric has llm_checks but judge_prompt not found: {p}")
        judge_prompt = _read_text(p)

    # white_prompt optional (do NOT require)
    white_prompt: Optional[str] = None
    if white_prompt_rel:
        p = _resolve_path(spec_dir, white_prompt_rel)
        if p.exists():
            white_prompt = _read_text(p)

    return {
        "rubric": rubric,
        "eval_ref": eval_ref,
        "judge_prompt": judge_prompt,
        "white_prompt": white_prompt,
    }
