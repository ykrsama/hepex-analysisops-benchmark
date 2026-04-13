from __future__ import annotations
from typing import Any


def mock_bundle_hyy_l1(task_id: str) -> dict[str, Any]:
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
                "task_id": task_id,
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
                    {"cut_id": "leading_photon_isolation", "applies_to": "leading_photon", "variable": "photon_ptcone20", "operator": "<", "value": 0.055, "depends_on": ["photon_ptcone20", "photon_pt"], "applied": True},
                    {"cut_id": "subleading_photon_isolation", "applies_to": "subleading_photon", "variable": "photon_ptcone20", "operator": "<", "value": 0.055, "depends_on": ["photon_ptcone20", "photon_pt"], "applied": True},
                    {"cut_id": "leading_photon_eta_transition_veto", "applies_to": "leading_photon", "variable": "abs_photon_eta", "operator": "interval_veto", "value": [1.37, 1.52], "interval": [1.37, 1.52], "applied": True},
                    {"cut_id": "subleading_photon_eta_transition_veto", "applies_to": "subleading_photon", "variable": "abs_photon_eta", "operator": "interval_veto", "value": [1.37, 1.52], "interval": [1.37, 1.52], "applied": True},
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


def mock_trace_zpeak_fit(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "ok",
        "fit_result": {
            "mu": 91.3,
            "sigma": 2.5,
            "gof": {"p_value": 0.2}
        },
        "fit_method": {
            "model": "BreitWigner ⊗ Gaussian + background(poly1)",
            "fit_range": [70, 110],
            "binned_or_unbinned": "binned",
            "optimizer": "iminuit",
            "initial_params": {"mu": 91.2, "sigma": 2.4},
            "uncertainties_method": "HESSE",
            "reasoning": "Standard Z peak fit using Breit-Wigner convolved with Gaussian to account for detector resolution."
        },
        "artifacts": [
            {"id":"fit_result", "kind":"json", "name":"fit_result.json"},
            {"id":"mass_hist", "kind":"histogram", "name":"m_mumu_hist.npz"}
        ]
    }

def mock_trace_hyy(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "ok",
        "fit_result": {
            "center": 125.4,
            "sigma": 2.3,
            "model": "Gaussian + Polynomial4"
        },
        "cuts": [
            {"cut_id":"tight_id","expression":"photon_isTightID"},
            {"cut_id":"pt_abs","expression":"photon_pt > threshold"},
            {"cut_id":"calo_iso","expression":"ptcone20/pt"},
            {"cut_id":"eta_crack_veto","expression":"exclude crack"},
            {"cut_id":"compute_myy","expression":"m_yy"},
            {"cut_id":"pt_rel_myy","expression":"pt/myy"}
        ],
        "cutflow": [
            {"cut_id":"tight_id","n_before":100000,"n_after":20000}
        ],
        # Add basic method/reasoning if hyy spec is updated later to require it
        "fit_method": {
            "model": "Gaussian + Poly4",
            "reasoning": "Classic sideband fit."
        },
        "artifacts": []
    }

def mock_trace_hmumu(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "ok",
        "fit_result": {
            "center": 125.2,
            "sigma": 2.8,
            "significance": 1.5,
            "model": "Signal + Background"
        },
        "fit_method": {
            "model": "Double Gaussian (Signal) + Exponential (Background)",
            "optimizer": "scipy.optimize.curve_fit",
            "fit_range": [110, 160],
            "reasoning": "Using VBF selection to enhance S/B. Vetoing b-jets effectively removes ttbar contamination. The exponential background models the Drell-Yan tail well."
        },
        "cuts": [
            {"cut_id":"trig","expression":"trigM"},
            {"cut_id":"2lep","expression":"lep_n == 2"},
            {"cut_id":"muon_type","expression":"type == 13"},
            {"cut_id":"pt_30","expression":"pt > 30"},
            {"cut_id":"met_80","expression":"met <= 80"},
            {"cut_id":"charge_opp","expression":"charge sum == 0"},
            {"cut_id":"id_iso","expression":"medium ID + loose iso"},
            {"cut_id":"jet_vbf","expression":"vbf cuts (mass>500)"},
            {"cut_id":"bjet_veto","expression":"veto b-jets"}
        ],
        "artifacts": []
    }

def mock_trace_hbb(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "ok",
        "fit_result": {
             "center": 125.0,
             "sigma": 15.0
        },
        "fit_method": {
             "model": "Invariant Mass Calculation",
             "reasoning": "High MET (>150) suppresses QCD. Angular cuts ensure Z boson recoil. 2 b-tags select H->bb."
        },
        "cuts": [
            {"cut_id":"met_trigger","expression":"trigMET"},
            {"cut_id":"met_150","expression":"met > 150"},
            {"cut_id":"zero_lep","expression":"n_lep == 0"},
            {"cut_id":"2_3_jets","expression":"n_jet in [2,3]"},
            {"cut_id":"2_bjets","expression":"n_bjet == 2"},
            {"cut_id":"lead_b_45","expression":"pt_b1 > 45"},
            {"cut_id":"ht_cut","expression":"HT > 120"},
            {"cut_id":"dphi_bb","expression":"dphi < 140"},
            {"cut_id":"dphi_met_bb","expression":"dphi > 120"},
            {"cut_id":"min_dphi_met_jet","expression":"dphi > 20"},
            {"cut_id":"mass_calc","expression":"m(bb)"}
        ],
        "artifacts": []
    }

def mock_trace_hzz(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "ok",
        "fit_result": {
            "center": 124.9,
            "sigma": 1.5,
            "model": "Gaussian"
        },
        "fit_method": {
            "model": "Crystal Ball + Polynomial",
            "reasoning": "Z1 is selected as the pair closest to Z mass. Z2 is the subleading pair. 4-lepton mass shows a clear peak."
        },
        "cuts": [
            {"cut_id":"4lep","expression":"n_lep == 4"},
            {"cut_id":"sfos_pairs","expression":"valid combination"},
            {"cut_id":"z1_mass","expression":"closest to 91.2"},
            {"cut_id":"z2_mass","expression":"12 < m < 115"}
        ],
        "artifacts": []
    }

def mock_trace_ttbar(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "ok",
        "fit_result": {
            "center": 172.5,
            "sigma": 15.0
        },
        "fit_method": {
            "model": "Kinematic Reconstruction",
            "reasoning": "Solved quadratic eq for neutrino Pz using W mass constraint. Used chi2 sorting to resolve jet combinatorics."
        },
        "cuts": [
            {"cut_id":"one_lep","expression":"n_lep == 1"},
            {"cut_id":"met_30","expression":"met > 30"},
            {"cut_id":"w_mt_30","expression":"mt > 30"},
            {"cut_id":"4_jets","expression":"n_jet >= 4"},
            {"cut_id":"2_bjets","expression":"n_bjet >= 2"},
            {"cut_id":"reconstruct_top","expression":"neutrino pz + top mass"}
        ],
        "artifacts": []
    }

def mock_trace_wz3l(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "ok",
        "fit_result": {
            "center": 91.2,
            "sigma": 3.0
        },
        "fit_method": {
            "model": "Z Mass Peak Check",
            "reasoning": "Selected SFOS pair closest to Z mass. Unpaired lepton + MET used for W mT."
        },
        "cuts": [
            {"cut_id":"3lep","expression":"n_lep == 3"},
            {"cut_id":"sfos_z_cand","expression":"sfos pair"},
            {"cut_id":"z_mass_window","expression":"81 < m < 101"},
            {"cut_id":"met_30","expression":"met > 30"},
            {"cut_id":"w_mt_30","expression":"mt > 30"},
            {"cut_id":"reconstruct_w_mass","expression":"w mass"}
        ],
        "artifacts": []
    }

MOCK_REGISTRY = {
    "zpeak_fit": mock_trace_zpeak_fit,
    "hyy_analysis": mock_trace_hyy,
    "hyy": mock_trace_hyy,
    "hmumu": mock_trace_hmumu,
    "hbb": mock_trace_hbb,
    "hzz": mock_trace_hzz,
    "ttbar": mock_trace_ttbar,
    "wz3l": mock_trace_wz3l,
}

def get_mock_trace(task_type: str, task_id: str) -> dict[str, Any]:
    handler = MOCK_REGISTRY.get(task_type)
    if handler:
        return handler(task_id)
    return {"task_id": task_id, "status": "error", "error": f"Unknown task type: {task_type}"}


MOCK_BUNDLE_REGISTRY = {
    "hyy_l1": mock_bundle_hyy_l1,
}


def get_mock_bundle(task_type: str, task_id: str) -> dict[str, Any]:
    handler = MOCK_BUNDLE_REGISTRY.get(task_type)
    if handler:
        return handler(task_id)
    return {
        "status": "error",
        "error": f"Unknown mock submission bundle task type: {task_type}",
        "artifacts": {},
    }
