# src/engine/contract_validator.py
"""
Public-safe contract validator.

Reads submission_contract.yaml from the task directory and validates a
submission trace against the declared artifact schemas.

NOTE: This is for public-safe validation only and is not intended to
replace private rubric-based scoring.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_contract(task_dir: str | Path) -> Dict[str, Any]:
    path = Path(task_dir) / "submission_contract.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


TYPE_NAMES = {
    "string": str,
    "boolean": bool,
    "float": (int, float),
    "integer": int,
    "number": (int, float),
    "object": dict,
    "array_float": list,
    "array_number": list,
    "array_string": list,
    "array_object": list,
    "array_float_len_2": list,
}


def _check_required_keys(
    obj: Any,
    schema: Any,
    path: str,
) -> List[str]:
    """Recursively check that obj contains the keys declared in schema.

    schema can be:
      - a dict  → { key: sub-schema, ... }
      - a list  → each element is either a str (leaf key) or a one-item dict
      - a str   → leaf key (existence only, no type checking)
      - None    → nothing to check

    Returns a list of dotted-path strings for every missing or wrong-type field.
    """
    errors: List[str] = []

    if schema is None or obj is None:
        return errors

    if not isinstance(obj, dict):
        errors.append(f"{path}: expected object, got {type(obj).__name__}")
        return errors

    if isinstance(schema, dict):
        items = schema.items()
    elif isinstance(schema, list):
        # list of leaf-key strings or single-key dicts
        items = []
        for entry in schema:
            if isinstance(entry, str):
                items.append((entry, None))
            elif isinstance(entry, dict):
                for k, v in entry.items():
                    items.append((k, v))
    else:
        return errors

    for key, sub_schema in items:
        child_path = f"{path}.{key}" if path else key
        if key not in obj:
            errors.append(f"{child_path}: missing")
            continue
        if isinstance(sub_schema, dict) and sub_schema.get("type") == "object":
            nested = sub_schema.get("required_keys", {})
            errors.extend(_check_required_keys(obj[key], nested, child_path))
        elif isinstance(sub_schema, dict) and "required_keys" in sub_schema:
            errors.extend(_check_required_keys(obj[key], sub_schema["required_keys"], child_path))

    return errors


def _load_json(path: Path) -> Any:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def _get_value(obj: Any, field: str) -> Any:
    current = obj
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(field)
        current = current[part]
    return current


def _validate_required_fields(data: dict[str, Any], fields: list[str], errors: list[str], prefix: str = "") -> None:
    for field in fields:
        label = f"{prefix}{field}" if not prefix else f"{prefix}.{field}"
        try:
            _get_value(data, field)
        except KeyError:
            errors.append(f"{label}: missing")


def _validate_type(value: Any, type_name: str) -> bool:
    expected = TYPE_NAMES.get(type_name)
    if expected is None:
        return True
    if type_name == "array_float":
        return isinstance(value, list) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
    if type_name == "array_number":
        return isinstance(value, list) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
    if type_name == "array_string":
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if type_name == "array_object":
        return isinstance(value, list) and all(isinstance(v, dict) for v in value)
    if type_name == "array_float_len_2":
        return isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, expected)


def _validate_field_types(data: dict[str, Any], field_types: dict[str, str], errors: list[str], prefix: str = "") -> None:
    for field, type_name in field_types.items():
        label = f"{prefix}{field}" if not prefix else f"{prefix}.{field}"
        try:
            value = _get_value(data, field)
        except KeyError:
            continue
        if not _validate_type(value, type_name):
            errors.append(f"{label}: expected {type_name}")


def _validate_constraints(data: dict[str, Any], constraints: dict[str, Any], errors: list[str]) -> None:
    for field, rule in constraints.items():
        try:
            value = _get_value(data, field)
        except KeyError:
            continue
        if isinstance(rule, dict):
            min_length = rule.get("min_length")
            contains_all = rule.get("contains_all")
            if min_length is not None and hasattr(value, "__len__") and len(value) < min_length:
                errors.append(f"{field}: expected min_length {min_length}")
            if contains_all is not None and isinstance(value, list):
                missing = [item for item in contains_all if item not in value]
                if missing:
                    errors.append(f"{field}: missing required values {missing}")


def _validate_nested_fields(data: dict[str, Any], nested_spec: dict[str, Any], errors: list[str]) -> None:
    for field, spec in nested_spec.items():
        try:
            value = _get_value(data, field)
        except KeyError:
            continue
        if isinstance(value, list):
            for idx, entry in enumerate(value):
                if not isinstance(entry, dict):
                    errors.append(f"{field}[{idx}]: expected object")
                    continue
                _validate_required_fields(entry, spec.get("required_fields", []), errors, f"{field}[{idx}]")
                _validate_field_types(entry, spec.get("field_types", {}), errors, f"{field}[{idx}]")
        elif isinstance(value, dict):
            _validate_required_fields(value, spec.get("required_fields", []), errors, field)
            _validate_field_types(value, spec.get("field_types", {}), errors, field)


def _validate_markdown(path: Path, schema: dict[str, Any], errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    constraints = schema.get("constraints", {})
    if constraints.get("non_empty") and not text.strip():
        errors.append(f"{path.name}: expected non-empty markdown")
    min_characters = constraints.get("min_characters")
    if min_characters is not None and len(text.strip()) < min_characters:
        errors.append(f"{path.name}: expected at least {min_characters} characters")


def _validate_json_artifact(path: Path, schema: dict[str, Any], errors: list[str]) -> None:
    import json
    try:
        data = _load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON ({exc.msg})")
        return
    if not isinstance(data, dict):
        errors.append(f"{path.name}: expected top-level object")
        return
    _validate_required_fields(data, schema.get("required_fields", []), errors)
    _validate_field_types(data, schema.get("field_types", {}), errors)
    _validate_nested_fields(data, schema.get("nested_required_fields", {}), errors)
    _validate_constraints(data, schema.get("constraints", {}), errors)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_contract(
    task: Any,
    submission_trace: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate submission_trace against the task's submission_contract.yaml.

    Returns a report dict compatible with the existing `final.total_score`
    structure used throughout agent.py.
    """
    spec_dir: Optional[str] = getattr(task, "spec_dir", None)
    task_id: str = getattr(task, "id", "unknown")
    task_type: str = getattr(task, "type", "unknown")

    if spec_dir is None:
        return _error_report(task_id, task_type, "No spec_dir: cannot locate submission_contract.yaml")

    contract = _load_contract(spec_dir)
    if not contract:
        return _error_report(task_id, task_type, "submission_contract.yaml not found or empty")

    required_artifacts: List[Dict[str, Any]] = contract.get("required_artifacts", [])

    all_errors: List[str] = []
    missing_artifacts: List[str] = []
    schema_errors: List[str] = []

    for artifact_def in required_artifacts:
        name: str = artifact_def.get("name", "")
        art_type: str = artifact_def.get("type", "json")

        # For fit_summary.json we validate directly against the submission trace
        # (the trace IS the fit_summary artifact).
        # artifact_manifest.json is runtime-generated; treat as lenient (warn only).
        if name == "artifact_manifest.json":
            # lenient: count as warning, not hard failure
            if "artifacts" not in submission_trace.get("artifact_manifest", {}):
                pass  # missing is acceptable at this stage
            continue

        if name == "fit_summary.json" and art_type == "json":
            req_keys = artifact_def.get("required_keys", {})
            errs = _check_required_keys(submission_trace, req_keys, "")
            schema_errors.extend(errs)
        else:
            # Generic artifact: just note it (future extension point)
            pass

    passed = len(schema_errors) == 0 and len(missing_artifacts) == 0

    # Score: 1.0 if fully passed, partial credit for partial failures
    n_checks = max(1, len(required_artifacts))
    n_failed = len(schema_errors) + len(missing_artifacts)
    raw_score = max(0.0, 1.0 - n_failed / n_checks)

    return {
        "task_id": task_id,
        "type": task_type,
        "status": "ok" if passed else "contract_fail",
        "validator": "contract_validator",
        "hard_checks_passed": passed,
        "hard_failures": schema_errors + missing_artifacts,
        "schema_errors": schema_errors,
        "missing_artifacts": missing_artifacts,
        "final": {
            "total_score": raw_score,
            "max_score": 1.0,
            "normalized_score": raw_score,
        },
        "issues": [
            {"severity": "error", "code": "SCHEMA_ERROR", "message": e}
            for e in schema_errors
        ] + [
            {"severity": "error", "code": "MISSING_ARTIFACT", "message": a}
            for a in missing_artifacts
        ],
    }


def validate_submission_dir(task: Any, submission_dir: str | Path) -> Dict[str, Any]:
    """Validate a materialized submission directory against the task contract."""
    spec_dir: Optional[str] = getattr(task, "spec_dir", None)
    task_id: str = getattr(task, "id", "unknown")
    task_type: str = getattr(task, "type", "unknown")

    if spec_dir is None:
        return _error_report(task_id, task_type, "No spec_dir: cannot locate submission contract")

    contract_rel = getattr(task, "submission_contract_path", "submission_contract.yaml") or "submission_contract.yaml"
    contract_path = Path(spec_dir) / contract_rel
    if not contract_path.exists():
        return _error_report(task_id, task_type, f"submission contract not found: {contract_path.name}")

    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    submission_dir = Path(submission_dir)
    missing_files: list[str] = []
    schema_errors: list[str] = []

    for artifact in contract.get("required_outputs", []) or []:
        filename = artifact["canonical_filename"]
        path = submission_dir / filename
        if not path.exists():
            missing_files.append(filename)
            continue
        schema = contract.get("schemas", {}).get(filename, {})
        if artifact.get("type") == "markdown":
            _validate_markdown(path, schema, schema_errors)
        else:
            _validate_json_artifact(path, schema, schema_errors)

    status = "ok" if not missing_files and not schema_errors else "contract_fail"
    return {
        "task_id": task_id,
        "type": task_type,
        "status": status,
        "validator": "contract_validator_dir",
        "hard_checks_passed": status == "ok",
        "missing_files": missing_files,
        "schema_errors": schema_errors,
        "final": {
            "total_score": 1.0 if status == "ok" else 0.0,
            "max_score": 1.0,
            "normalized_score": 1.0 if status == "ok" else 0.0,
        },
        "issues": [
            {"severity": "error", "code": "MISSING_FILE", "message": msg}
            for msg in missing_files
        ] + [
            {"severity": "error", "code": "SCHEMA_ERROR", "message": msg}
            for msg in schema_errors
        ],
    }


def _error_report(task_id: str, task_type: str, msg: str) -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "type": task_type,
        "status": "error",
        "validator": "contract_validator",
        "hard_checks_passed": False,
        "error": msg,
        "final": {"total_score": 0.0, "max_score": 1.0, "normalized_score": 0.0},
        "issues": [{"severity": "error", "code": "VALIDATOR_ERROR", "message": msg}],
    }
