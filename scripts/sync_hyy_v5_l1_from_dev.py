#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_ROOT = REPO_ROOT.parent / "hepex-analysisops-dev" / "benchmark" / "tasks" / "Hyy_v5" / "l1_package_finetune"
TARGET_ROOT = REPO_ROOT / "tasks_public" / "t002_hyy_v5_l1"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def build_normalized_prompt(source_prompt: str) -> str:
    prompt = source_prompt.replace("fit_model_used", "fit_model_family_used")
    if "object_definition" not in prompt:
        prompt = prompt.replace(
            "- baseline_assumptions_used\n",
            "- baseline_assumptions_used\n- object_definition\n- derived_observables\n- primary_observable\n- histogram_definition\n",
        )
    if "shared_input_dir" not in prompt:
        prompt += (
            "\n\n---\n\n# 12. Runtime Input Rules\n\n"
            "If `shared_input_dir` is provided, treat it as read-only input.\n"
            "Do not modify dataset files in place.\n"
            "Return outputs through `submission_bundle_v1` as small structured artifacts only.\n"
        )
    return prompt


def build_normalized_contract(source_contract: dict[str, Any]) -> dict[str, Any]:
    contract = dict(source_contract)
    schemas = dict(contract.get("schemas", {}) or {})
    trace_schema = dict(schemas.get("submission_trace.json", {}) or {})
    required_fields = list(trace_schema.get("required_fields", []) or [])
    required_fields = [
        "fit_model_family_used" if field == "fit_model_used" else field
        for field in required_fields
    ]
    for field in [
        "baseline_assumptions_used",
        "object_definition",
        "derived_observables",
        "primary_observable",
        "histogram_definition",
        "fit_model_family_used",
    ]:
        if field not in required_fields:
            required_fields.append(field)
    trace_schema["required_fields"] = required_fields
    nested = dict(trace_schema.get("nested_required_fields", {}) or {})
    if "fit_model_used" in nested and "fit_model_family_used" not in nested:
        nested["fit_model_family_used"] = nested.pop("fit_model_used")
    nested["object_definition"] = {"required_fields": ["type", "multiplicity", "ordering_principle"]}
    nested["primary_observable"] = {"required_fields": ["name", "inputs", "construction"]}
    nested["histogram_definition"] = {"required_fields": ["observable", "range", "bin_width", "uncertainty_model"]}
    nested["fit_model_family_used"] = {"required_fields": ["signal", "background", "background_order", "fit_range_GeV", "weighting_scheme"]}
    trace_schema["nested_required_fields"] = nested
    field_types = dict(trace_schema.get("field_types", {}) or {})
    if "fit_model_used" in field_types and "fit_model_family_used" not in field_types:
        field_types["fit_model_family_used"] = field_types.pop("fit_model_used")
    field_types.update(
        {
            "baseline_assumptions_used": "array_string",
            "derived_observables": "array_object",
            "primary_observable": "object",
            "histogram_definition": "object",
            "fit_model_family_used": "object",
        }
    )
    trace_schema["field_types"] = field_types
    schemas["submission_trace.json"] = trace_schema
    contract["schemas"] = schemas
    return contract


def main() -> None:
    prompt_path = DEV_ROOT / "executor_prompt.md"
    contract_path = DEV_ROOT / "submission_contract_l1.yaml"
    ensure(prompt_path.exists(), f"Missing source prompt: {prompt_path}")
    ensure(contract_path.exists(), f"Missing source contract: {contract_path}")

    source_prompt = prompt_path.read_text(encoding="utf-8")
    source_contract = load_yaml(contract_path)
    required_outputs = [entry.get("canonical_filename") for entry in source_contract.get("required_outputs", [])]
    ensure(
        required_outputs == [
            "diphoton_mass_spectrum.json",
            "diphoton_fit_summary.json",
            "data_minus_background.json",
            "interpretation.md",
            "submission_trace.json",
        ],
        "Finetuned L1 contract required outputs do not match the expected Hyy V5 L1 filenames.",
    )
    ensure("reported_result" in (source_contract.get("schemas", {}).get("submission_trace.json", {}).get("required_fields", []) or []),
           "Finetuned L1 contract is missing reported_result in submission_trace.json.")

    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    (TARGET_ROOT / "solver_prompt.md").write_text(build_normalized_prompt(source_prompt), encoding="utf-8")
    (TARGET_ROOT / "submission_contract.yaml").write_text(
        yaml.safe_dump(build_normalized_contract(source_contract), sort_keys=False),
        encoding="utf-8",
    )
    print(f"Synced normalized Hyy V5 L1 assets into {TARGET_ROOT}")


if __name__ == "__main__":
    main()
