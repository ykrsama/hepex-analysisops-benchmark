from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
import yaml

from a2a.utils import new_agent_text_message

from agent import Agent
from engine.contract_validator import validate_submission_dir
from engine.input_access import InputAccessError, resolve_input_access
from engine.package_loader import load_submission_contract
from engine.secret_store import SecretStore
from engine.submission_bundle import SubmissionBundleError, parse_submission_bundle
from tasks.task_spec import GreenConfig, load_task_spec


TASK_DIR = Path(__file__).parent.parent / "tasks_public" / "t002_hyy_v5_l1"
LEGACY_TASK_DIR = Path(__file__).parent.parent / "tasks_public" / "t001_zpeak_fit"


def sample_submission_bundle() -> dict:
    return {
        "status": "ok",
        "artifacts": {
            "diphoton_mass_spectrum.json": {
                "bin_edges": [100.0, 101.0, 102.0],
                "bin_counts": [4, 7],
                "bin_uncertainties": [2.0, 2.6458],
            },
            "diphoton_fit_summary.json": {
                "signal_model_family": "gaussian",
                "background_model_family": "polynomial",
                "fit_range": [100.0, 160.0],
                "signal_peak_position": 125.1,
            },
            "data_minus_background.json": {
                "bin_centers": [124.5, 125.5],
                "residual_counts": [0.2, 1.7],
                "residual_uncertainties": [0.5, 0.6],
            },
            "interpretation.md": "A Higgs-like excess is observed near 125.1 GeV in the diphoton spectrum.",
            "submission_trace.json": {
                "workflow_stages": [
                    {"stage_id": "data_loading", "order_index": 1, "status": "ok", "depends_on": []},
                    {"stage_id": "event_selection", "order_index": 2, "status": "ok", "depends_on": ["data_loading"]},
                    {"stage_id": "diphoton_mass_construction", "order_index": 3, "status": "ok", "depends_on": ["event_selection"]},
                    {"stage_id": "spectrum_histogramming", "order_index": 4, "status": "ok", "depends_on": ["diphoton_mass_construction"]},
                    {"stage_id": "uncertainty_assignment", "order_index": 5, "status": "ok", "depends_on": ["spectrum_histogramming"]},
                    {"stage_id": "spectrum_fitting", "order_index": 6, "status": "ok", "depends_on": ["uncertainty_assignment"]},
                    {"stage_id": "signal_interpretation", "order_index": 7, "status": "ok", "depends_on": ["spectrum_fitting"]},
                ],
                "baseline_assumptions_used": [
                    "photon indices 0 and 1 correspond to the ordered leading/subleading pair",
                ],
                "object_definition": {
                    "type": "photon_pair",
                    "multiplicity": 2,
                    "ordering_principle": "leading_subleading_photon_pair",
                    "baseline_assumption": {
                        "leading_photon_index": 0,
                        "subleading_photon_index": 1,
                    },
                },
                "cuts_applied": [
                    {"cut_id": "at_least_two_photons", "applies_to": "event", "variable": "photon_count", "operator": ">=", "value": 2, "applied": True},
                    {"cut_id": "leading_photon_tight_id", "applies_to": "leading_photon", "variable": "photon_isTightID", "operator": "==", "value": True, "applied": True},
                    {"cut_id": "subleading_photon_tight_id", "applies_to": "subleading_photon", "variable": "photon_isTightID", "operator": "==", "value": True, "applied": True},
                    {"cut_id": "leading_photon_pt", "applies_to": "leading_photon", "variable": "photon_pt", "operator": ">", "value": 50.0, "applied": True},
                    {"cut_id": "subleading_photon_pt", "applies_to": "subleading_photon", "variable": "photon_pt", "operator": ">", "value": 30.0, "applied": True},
                    {"cut_id": "leading_photon_isolation", "applies_to": "leading_photon", "variable": "photon_ptcone20", "operator": "<", "value": 0.055, "applied": True},
                    {"cut_id": "subleading_photon_isolation", "applies_to": "subleading_photon", "variable": "photon_ptcone20", "operator": "<", "value": 0.055, "applied": True},
                    {"cut_id": "leading_photon_eta_transition_veto", "applies_to": "leading_photon", "variable": "abs_photon_eta", "operator": "interval_veto", "value": [1.37, 1.52], "applied": True},
                    {"cut_id": "subleading_photon_eta_transition_veto", "applies_to": "subleading_photon", "variable": "abs_photon_eta", "operator": "interval_veto", "value": [1.37, 1.52], "applied": True},
                    {"cut_id": "diphoton_mass_nonzero", "applies_to": "diphoton_pair", "variable": "m_yy", "operator": "!=", "value": 0.0, "applied": True},
                    {"cut_id": "leading_photon_pt_over_m_yy", "applies_to": "leading_photon", "variable": "photon_pt_over_m_yy", "operator": ">", "value": 0.35, "applied": True},
                    {"cut_id": "subleading_photon_pt_over_m_yy", "applies_to": "subleading_photon", "variable": "photon_pt_over_m_yy", "operator": ">", "value": 0.35, "applied": True},
                ],
                "derived_observables": [
                    {"name": "abs_photon_eta", "depends_on": ["photon_eta"]},
                    {"name": "m_yy", "depends_on": ["photon_pt", "photon_eta", "photon_phi", "photon_e"]},
                    {"name": "photon_pt_over_m_yy", "depends_on": ["photon_pt", "m_yy"]},
                ],
                "observable_constructed": {
                    "name": "m_yy",
                    "inputs": ["photon_pt", "photon_eta", "photon_phi", "photon_e"],
                    "formula_summary": "invariant mass of the first two photon four-vectors",
                },
                "primary_observable": {
                    "name": "m_yy",
                    "inputs": ["photon_pt", "photon_eta", "photon_phi", "photon_e"],
                    "construction": "invariant_mass_of_first_two_photon_four_vectors",
                },
                "histogram_definition": {
                    "observable": "m_yy",
                    "range": [100.0, 160.0],
                    "bin_width": 1.0,
                    "uncertainty_model": "sqrt_n_statistical_uncertainty",
                },
                "fit_model_family_used": {
                    "signal": "gaussian",
                    "background": "polynomial",
                    "background_order": 4,
                    "fit_range_GeV": [100.0, 160.0],
                    "weighting_scheme": "inverse_sqrt_bin_count",
                },
                "output_files_generated": [
                    "diphoton_mass_spectrum.json",
                    "diphoton_fit_summary.json",
                    "data_minus_background.json",
                    "interpretation.md",
                    "submission_trace.json",
                ],
                "reported_result": {
                    "signal_peak_position": 125.1,
                },
            },
        },
    }


def sample_private_rubric() -> dict:
    return {
        "version": 1,
        "weights": {
            "execution": 0.4,
            "pipeline": 0.3,
            "analysis": 0.3,
            "validation": 0.0,
        },
        "checks": {
            "execution": [
                {
                    "id": "required_outputs_present",
                    "type": "deterministic",
                    "condition": {
                        "required_outputs": [
                            {"canonical_filename": "diphoton_mass_spectrum.json"},
                            {"canonical_filename": "diphoton_fit_summary.json"},
                            {"canonical_filename": "data_minus_background.json"},
                            {"canonical_filename": "interpretation.md"},
                            {"canonical_filename": "submission_trace.json"},
                        ],
                    },
                    "score": 1.0,
                }
            ],
            "pipeline": [
                {
                    "id": "required_stages_present",
                    "type": "structural",
                    "condition": {
                        "required_stages": [
                            "data_loading",
                            "event_selection",
                            "diphoton_mass_construction",
                            "spectrum_histogramming",
                            "uncertainty_assignment",
                            "spectrum_fitting",
                            "signal_interpretation",
                        ]
                    },
                    "score": 1.0,
                }
            ],
            "analysis": [
                {
                    "id": "peak_range",
                    "type": "deterministic",
                    "condition": {
                        "artifact_id": "diphoton_fit_summary",
                        "field": "signal_peak_position",
                        "expected_range": [123.0, 127.0],
                    },
                    "score": 1.0,
                }
            ],
            "validation": [],
        },
    }


def test_task_spec_capability_defaults_for_legacy_task():
    task = load_task_spec(LEGACY_TASK_DIR)
    assert task.input_strategy == "download"
    assert task.solver_response_mode == "submission_trace"
    assert task.evaluation_mode == "legacy_trace_contract"


def test_task_spec_capability_overrides_for_hyy_task():
    task = load_task_spec(TASK_DIR)
    assert task.input_strategy == "shared_manifest"
    assert task.solver_response_mode == "submission_bundle_v1"
    assert task.evaluation_mode == "directory_contract_and_private_l1"


class DummyUpdater:
    def __init__(self):
        self.status_updates = []
        self.artifacts = []
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


def make_secret_store_payload(task_spec) -> str:
    contract = load_submission_contract(task_spec)
    contract_hash = SecretStore("").contract_hash(contract)
    rubric_b64 = base64.b64encode(yaml.safe_dump(sample_private_rubric(), sort_keys=False).encode("utf-8")).decode("utf-8")
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


def test_resolve_input_access_requires_static_mount(tmp_path):
    task = load_task_spec(TASK_DIR)
    cfg = GreenConfig(task_dirs=[str(TASK_DIR)])
    with pytest.raises(InputAccessError):
        resolve_input_access(task, cfg)


def test_validate_task_capabilities_rejects_missing_contract_for_bundle_mode(tmp_path):
    task = load_task_spec(TASK_DIR).model_copy(update={"submission_contract_path": None})
    cfg = GreenConfig(
        task_dirs=[str(TASK_DIR)],
        input_access_mode="local_shared_mount",
        shared_input_dir=str(tmp_path),
        input_manifest_path=str(tmp_path / "input_manifest.json"),
        allow_green_download=False,
    )
    agent = Agent()
    with pytest.raises(SubmissionBundleError):
        agent._validate_task_capabilities(task, cfg)


def test_parse_submission_bundle_rejects_large_payload():
    contract = load_submission_contract(load_task_spec(TASK_DIR))
    bundle = sample_submission_bundle()
    bundle["artifacts"]["interpretation.md"] = "x" * (600 * 1024)
    with pytest.raises(SubmissionBundleError):
        parse_submission_bundle(bundle, contract)


def test_validate_submission_dir_hyy_v5_l1(tmp_path):
    task = load_task_spec(TASK_DIR)
    bundle = sample_submission_bundle()
    for filename, payload in bundle["artifacts"].items():
        path = tmp_path / filename
        if filename.endswith(".md"):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
    report = validate_submission_dir(task, tmp_path)
    assert report["status"] == "ok"
    assert report["schema_errors"] == []
    assert report["missing_files"] == []


@pytest.mark.asyncio
async def test_agent_hyy_v5_l1_submission_bundle_flow(monkeypatch, tmp_path):
    shared_input = tmp_path / "shared_input"
    shared_input.mkdir()
    (shared_input / "events.root").write_text("placeholder", encoding="utf-8")

    task = load_task_spec(TASK_DIR)
    captured = {}

    async def fake_talk_to_agent(self, message, url, new_conversation=True, timeout=300):
        captured["message"] = json.loads(message)
        return json.dumps(sample_submission_bundle())

    monkeypatch.setattr("messenger.Messenger.talk_to_agent", fake_talk_to_agent)
    monkeypatch.setenv("GREEN_SECRETS_JSON", make_secret_store_payload(task))

    req = {
        "participants": {"white_agent": "http://example.com"},
        "config": {
            "task_dirs": [str(TASK_DIR)],
            "data_dir": str(tmp_path / "runs"),
            "input_access_mode": "local_shared_mount",
            "shared_input_dir": str(shared_input),
            "input_manifest_path": str(shared_input / "input_manifest.json"),
            "allow_green_download": False,
        },
    }

    updater = DummyUpdater()
    agent = Agent()
    monkeypatch.setattr(agent, "_build_secret_backed_judge", lambda secret_store: None)
    await agent.run(new_agent_text_message(json.dumps(req)), updater)

    assert updater.rejected is None
    payload = captured["message"]
    assert "task_spec" not in payload
    assert payload["submission_contract"]["required_outputs"][0]["canonical_filename"] == "diphoton_mass_spectrum.json"
    assert payload["data"]["shared_input_dir"] == str(shared_input)
    assert payload["data"]["read_only_for_solver"] is True

    runs_root = Path(req["config"]["data_dir"]) / "runs"
    run_dirs = [path for path in runs_root.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    task_dir = run_dirs[0] / task.id
    assert (task_dir / "submission_bundle_raw.json").exists()
    assert (task_dir / "input_manifest.json").exists() is False
    assert (task_dir / "diphoton_fit_summary.json").exists()
    assert (shared_input / "input_manifest.json").exists()

    report = json.loads((task_dir / "judge_output.json").read_text(encoding="utf-8"))
    assert report["status"] == "ok"
    assert report["hard_checks_passed"] is True
    assert report["final"]["total_score"] > 0.0


@pytest.mark.asyncio
async def test_agent_routes_by_capability_not_task_id(monkeypatch, tmp_path):
    shared_input = tmp_path / "shared_input"
    shared_input.mkdir()
    (shared_input / "events.root").write_text("placeholder", encoding="utf-8")

    task = load_task_spec(TASK_DIR).model_copy(update={"id": "t999_custom_l1"})
    captured = {"prepare": 0, "trace": 0, "bundle": 0, "eval": 0}

    monkeypatch.setattr("agent.load_task_spec", lambda _: task)

    async def fake_prepare(self, task, cfg, base_data_dir, task_eval_dir, updater):
        captured["prepare"] += 1
        return (
            {
                "shared_input_dir": str(shared_input),
                "input_manifest_path": str(shared_input / "input_manifest.json"),
                "n_files": 1,
            },
            {
                "shared_input_dir": str(shared_input),
                "input_manifest_path": str(shared_input / "input_manifest.json"),
                "files": [{"logical_name": "events.root", "path": str(shared_input / "events.root"), "size_bytes": 11}],
            },
        )

    async def fake_bundle(self, task, request, task_eval_dir, data_info, input_manifest):
        captured["bundle"] += 1
        submission_trace = sample_submission_bundle()["artifacts"]["submission_trace.json"]
        (task_eval_dir / "submission_trace.json").write_text(json.dumps(submission_trace), encoding="utf-8")
        return {"submission_trace": submission_trace}

    async def fake_trace(self, task, request, data_info):
        captured["trace"] += 1
        return {"task_id": task.id, "status": "ok"}

    def fake_evaluate(self, task, task_eval_dir, submission_trace, data_info):
        captured["eval"] += 1
        return {
            "task_id": task.id,
            "type": task.type,
            "status": "ok",
            "hard_checks_passed": True,
            "final": {"total_score": 1.0, "max_score": 1.0, "normalized_score": 1.0},
        }

    monkeypatch.setattr(Agent, "_prepare_task_input", fake_prepare)
    monkeypatch.setattr(Agent, "_collect_solver_output", fake_bundle)
    monkeypatch.setattr(Agent, "_get_submission_trace", fake_trace)
    monkeypatch.setattr(Agent, "_evaluate_submission", fake_evaluate)

    req = {
        "participants": {"purple_agent": "http://example.com"},
        "config": {
            "task_dirs": [str(TASK_DIR)],
            "data_dir": str(tmp_path / "runs"),
            "input_access_mode": "local_shared_mount",
            "shared_input_dir": str(shared_input),
            "input_manifest_path": str(shared_input / "input_manifest.json"),
            "allow_green_download": False,
        },
    }

    updater = DummyUpdater()
    agent = Agent()
    await agent.run(new_agent_text_message(json.dumps(req)), updater)

    assert updater.rejected is None
    assert captured == {"prepare": 1, "trace": 0, "bundle": 1, "eval": 1}
