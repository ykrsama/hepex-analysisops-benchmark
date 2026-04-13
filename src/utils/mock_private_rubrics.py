from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEV_HYY_L1_PRIVATE_RUBRIC = (
    Path(__file__).resolve().parents[3]
    / "hepex-analysisops-dev"
    / "benchmark"
    / "tasks"
    / "Hyy_v5"
    / "l1_package_finetune"
    / "private_rubric.yaml"
)


def _embedded_hyy_l1_private_rubric() -> dict[str, Any]:
    """Reference private rubric used for local mock-scored Hyy L1 runs."""
    return {
        "version": 1,
        "weights": {
            "execution": 0.35,
            "pipeline": 0.2,
            "implementation": 0.25,
            "reasoning": 0.1,
            "analysis": 0.1,
            "validation": 0.0,
        },
        "checks": {
            "execution": [
                {
                    "id": "output_diphoton_mass_spectrum_present",
                    "type": "deterministic",
                    "description": "required diphoton mass spectrum artifact is present",
                    "condition": {
                        "required_outputs": [
                            {
                                "artifact_id": "diphoton_mass_spectrum",
                                "canonical_filename": "diphoton_mass_spectrum.json",
                            }
                        ],
                        "match": "all_present",
                    },
                    "score": 0.25,
                },
                {
                    "id": "output_diphoton_fit_summary_present",
                    "type": "deterministic",
                    "description": "required diphoton fit summary artifact is present",
                    "condition": {
                        "required_outputs": [
                            {
                                "artifact_id": "diphoton_fit_summary",
                                "canonical_filename": "diphoton_fit_summary.json",
                            }
                        ],
                        "match": "all_present",
                    },
                    "score": 0.25,
                },
                {
                    "id": "output_data_minus_background_present",
                    "type": "deterministic",
                    "description": "required residual artifact is present",
                    "condition": {
                        "required_outputs": [
                            {
                                "artifact_id": "data_minus_background",
                                "canonical_filename": "data_minus_background.json",
                            }
                        ],
                        "match": "all_present",
                    },
                    "score": 0.25,
                },
                {
                    "id": "output_interpretation_present",
                    "type": "deterministic",
                    "description": "required interpretation artifact is present",
                    "condition": {
                        "required_outputs": [
                            {
                                "artifact_id": "interpretation",
                                "canonical_filename": "interpretation.md",
                            }
                        ],
                        "match": "all_present",
                    },
                    "score": 0.25,
                },
                {
                    "id": "output_submission_trace_present",
                    "type": "deterministic",
                    "description": "required submission_trace artifact is present",
                    "condition": {
                        "required_outputs": [
                            {
                                "artifact_id": "submission_trace",
                                "canonical_filename": "submission_trace.json",
                            }
                        ],
                        "match": "all_present",
                    },
                    "score": 0.25,
                },
            ],
            "pipeline": [
                {
                    "id": "required_stages_present",
                    "type": "structural",
                    "description": "all required baseline workflow stages are present in the execution trace",
                    "condition": {
                        "evidence_source": "submission_trace",
                        "required_stages": [
                            "data_loading",
                            "event_selection",
                            "diphoton_mass_construction",
                            "spectrum_histogramming",
                            "uncertainty_assignment",
                            "spectrum_fitting",
                            "signal_interpretation",
                        ],
                        "match": "all_present",
                    },
                    "score": 0.4,
                },
                {
                    "id": "required_stage_ordering",
                    "type": "structural",
                    "description": "required baseline workflow stage ordering is satisfied",
                    "condition": {
                        "evidence_source": "submission_trace",
                        "ordered_stage_pairs": [
                            ["data_loading", "event_selection"],
                            ["event_selection", "diphoton_mass_construction"],
                            ["diphoton_mass_construction", "spectrum_histogramming"],
                            ["spectrum_histogramming", "uncertainty_assignment"],
                            ["uncertainty_assignment", "spectrum_fitting"],
                            ["spectrum_fitting", "signal_interpretation"],
                        ],
                        "match": "all_ordered",
                    },
                    "score": 0.3,
                },
                {
                    "id": "required_stage_dependencies",
                    "type": "structural",
                    "description": "required baseline workflow stage dependencies are satisfied",
                    "condition": {
                        "evidence_source": "submission_trace",
                        "dependencies": [
                            {"stage_id": "event_selection", "depends_on": ["data_loading"]},
                            {"stage_id": "diphoton_mass_construction", "depends_on": ["event_selection"]},
                            {"stage_id": "spectrum_histogramming", "depends_on": ["diphoton_mass_construction"]},
                            {"stage_id": "uncertainty_assignment", "depends_on": ["spectrum_histogramming"]},
                            {"stage_id": "spectrum_fitting", "depends_on": ["uncertainty_assignment"]},
                            {"stage_id": "signal_interpretation", "depends_on": ["spectrum_fitting"]},
                        ],
                        "match": "all_satisfied",
                    },
                    "score": 0.3,
                },
            ],
            "implementation": [
                {
                    "id": "baseline_object_definition_correct",
                    "type": "deterministic",
                    "description": "selected photon pair object definition matches baseline",
                    "condition": {
                        "object_definition": {
                            "type": "photon_pair",
                            "multiplicity": 2,
                            "ordering_principle": "leading_subleading_photon_pair",
                            "baseline_assumption": {
                                "leading_photon_index": 0,
                                "subleading_photon_index": 1,
                            },
                        },
                        "match": "exact",
                    },
                    "score": 0.1,
                },
                {
                    "id": "baseline_selection_cuts_correct",
                    "type": "deterministic",
                    "description": "all baseline selection cuts and thresholds match task specification",
                    "condition": {
                        "selection_cuts": [
                            {
                                "cut_id": "at_least_two_photons",
                                "applies_to": "event",
                                "variable": "photon_count",
                                "operator": ">=",
                                "value": 2,
                            },
                            {
                                "cut_id": "leading_photon_tight_id",
                                "applies_to": "leading_photon",
                                "variable": "photon_isTightID",
                                "operator": "==",
                                "value": True,
                            },
                            {
                                "cut_id": "subleading_photon_tight_id",
                                "applies_to": "subleading_photon",
                                "variable": "photon_isTightID",
                                "operator": "==",
                                "value": True,
                            },
                            {
                                "cut_id": "leading_photon_pt",
                                "applies_to": "leading_photon",
                                "variable": "photon_pt",
                                "operator": ">",
                                "value": 50.0,
                            },
                            {
                                "cut_id": "subleading_photon_pt",
                                "applies_to": "subleading_photon",
                                "variable": "photon_pt",
                                "operator": ">",
                                "value": 30.0,
                            },
                            {
                                "cut_id": "leading_photon_isolation",
                                "applies_to": "leading_photon",
                                "variable": "photon_ptcone20",
                                "operator": "<",
                                "value": 0.055,
                                "depends_on": ["photon_ptcone20", "photon_pt"],
                            },
                            {
                                "cut_id": "subleading_photon_isolation",
                                "applies_to": "subleading_photon",
                                "variable": "photon_ptcone20",
                                "operator": "<",
                                "value": 0.055,
                                "depends_on": ["photon_ptcone20", "photon_pt"],
                            },
                            {
                                "cut_id": "leading_photon_eta_transition_veto",
                                "applies_to": "leading_photon",
                                "variable": "abs_photon_eta",
                                "operator": "interval_veto",
                                "interval": [1.37, 1.52],
                            },
                            {
                                "cut_id": "subleading_photon_eta_transition_veto",
                                "applies_to": "subleading_photon",
                                "variable": "abs_photon_eta",
                                "operator": "interval_veto",
                                "interval": [1.37, 1.52],
                            },
                            {
                                "cut_id": "diphoton_mass_nonzero",
                                "applies_to": "diphoton_pair",
                                "variable": "m_yy",
                                "operator": "!=",
                                "value": 0.0,
                            },
                            {
                                "cut_id": "leading_photon_pt_over_m_yy",
                                "applies_to": "leading_photon",
                                "variable": "photon_pt_over_m_yy",
                                "operator": ">",
                                "value": 0.35,
                            },
                            {
                                "cut_id": "subleading_photon_pt_over_m_yy",
                                "applies_to": "subleading_photon",
                                "variable": "photon_pt_over_m_yy",
                                "operator": ">",
                                "value": 0.35,
                            },
                        ],
                        "match": "exact",
                    },
                    "score": 0.55,
                },
                {
                    "id": "observable_and_histogram_construction_correct",
                    "type": "deterministic",
                    "description": "observable construction and histogram configuration match baseline",
                    "condition": {
                        "derived_observables": [
                            {"name": "abs_photon_eta", "depends_on": ["photon_eta"]},
                            {
                                "name": "m_yy",
                                "depends_on": ["photon_pt", "photon_eta", "photon_phi", "photon_e"],
                            },
                            {"name": "photon_pt_over_m_yy", "depends_on": ["photon_pt", "m_yy"]},
                        ],
                        "primary_observable": {
                            "name": "m_yy",
                            "inputs": ["photon_pt", "photon_eta", "photon_phi", "photon_e"],
                            "construction": "invariant_mass_of_first_two_photon_four_vectors",
                        },
                        "histogram": {
                            "observable": "m_yy",
                            "range": [100.0, 160.0],
                            "bin_width": 1.0,
                            "uncertainty_model": "sqrt_n_statistical_uncertainty",
                        },
                        "match": "exact",
                    },
                    "score": 0.2,
                },
                {
                    "id": "fit_model_family_and_configuration_correct",
                    "type": "deterministic",
                    "description": "fit model family usage and fit configuration match baseline",
                    "condition": {
                        "inference": {
                            "method_type": "fit",
                            "signal_model": {"family": "gaussian"},
                            "background_model": {"family": "polynomial", "order": 4},
                            "fit_range": [100.0, 160.0],
                            "weighting": {"scheme": "inverse_sqrt_bin_count"},
                        },
                        "match": "exact",
                    },
                    "score": 0.15,
                },
            ],
            "reasoning": [
                {
                    "id": "interpretation_logically_consistent",
                    "type": "llm_judge",
                    "description": "interpretation is logically consistent with the reported fit and residual evidence",
                    "condition": {
                        "evidence_inputs": [
                            {"artifact_id": "interpretation"},
                            {"artifact_id": "diphoton_fit_summary"},
                            {"artifact_id": "data_minus_background"},
                        ],
                        "judge_rubric": {
                            "consistency_requirements": [
                                "aligns_with_signal_interpretation_stage",
                                "aligns_with_higgs_like_diphoton_excess_claim",
                                "consistent_with_reported_signal_peak_position",
                                "consistent_with_residual_excess_pattern",
                                "no_internal_contradiction",
                            ],
                            "forbidden_considerations": [
                                "numeric_accuracy",
                                "output_presence",
                            ],
                        },
                        "passing_mode": "binary",
                    },
                    "score": 1.0,
                }
            ],
            "analysis": [
                {
                    "id": "fitted_peak_position_in_expected_range",
                    "type": "deterministic",
                    "description": "fitted signal peak position lies in the expected Higgs-like region",
                    "condition": {
                        "artifact_id": "diphoton_fit_summary",
                        "field": "signal_peak_position",
                        "expected_range": [123.0, 127.0],
                        "inclusive": True,
                    },
                    "score": 0.5,
                },
                {
                    "id": "residual_excess_localized_in_region_of_interest",
                    "type": "heuristic",
                    "description": "residual spectrum shows a localized positive excess in the expected region",
                    "condition": {
                        "artifact_id": "data_minus_background",
                        "x_field": "bin_centers",
                        "y_field": "residual_counts",
                        "uncertainty_field": "residual_uncertainties",
                        "signal_type": "localized_excess",
                        "region_of_interest": [120.0, 130.0],
                        "preferred_center_range": [123.0, 127.0],
                    },
                    "score": 0.5,
                },
            ],
            "validation": [],
        },
    }


def hyy_l1_private_rubric() -> dict[str, Any]:
    """Prefer the dev reference rubric when available, otherwise use the embedded copy."""
    if DEV_HYY_L1_PRIVATE_RUBRIC.exists():
        obj = yaml.safe_load(DEV_HYY_L1_PRIVATE_RUBRIC.read_text(encoding="utf-8")) or {}
        if isinstance(obj, dict):
            return obj
    return _embedded_hyy_l1_private_rubric()
