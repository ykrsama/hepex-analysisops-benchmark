# 1. Objective

Rediscover the Higgs boson in the diphoton channel by reconstructing the diphoton invariant-mass spectrum (m_γγ) and testing for a localized Higgs-like excess near 125 GeV.

---

# 2. Top-level Workflow (Strict Execution)

Reproduce the baseline workflow exactly in this order:

1. data_loading  
2. event_selection  
3. diphoton_mass_construction  
4. spectrum_histogramming  
5. uncertainty_assignment  
6. spectrum_fitting  
7. signal_interpretation  

This is a test about if you can strictly and faithfully follow user's instruction, so Do NOT reorder, skip, or redesign stages.

---

# 3. Dataset

Use ATLAS Open Data:

- Release: 2025e-13tev-beta
- Sample: GamGam
- Mode: diphoton_skim

Combine all specified 2015–2016 periods into a single spectrum.

---

# 4. Event/Object Selection (Exact Baseline)

Use the leading and subleading photons.

Baseline assumption:
- photon indices 0 and 1 correspond to the ordered leading/subleading pair in this dataset

Do NOT search for alternative pairings.

Apply ALL cuts exactly (cut_id and criteria):

- `at_least_two_photons`: photon_count >= 2
- `leading_photon_tight_id`: leading photon tight ID == true
- `subleading_photon_tight_id`: subleading photon tight ID == true
- `leading_photon_pt`: leading photon pt > 50 GeV
- `subleading_photon_pt`: subleading photon pt > 30 GeV
- `leading_photon_isolation`: leading photon isolation ratio < 0.055
- `subleading_photon_isolation`: subleading photon isolation ratio < 0.055
- `leading_photon_eta_transition_veto`: abs(leading photon eta) not in [1.37, 1.52]
- `subleading_photon_eta_transition_veto`: abs(subleading photon eta) not in [1.37, 1.52]
- `diphoton_mass_nonzero`: m_yy != 0
- `leading_photon_pt_over_m_yy`: pt / m_yy > 0.35
- `subleading_photon_pt_over_m_yy`: pt / m_yy > 0.25

Do NOT modify cut_id, thresholds or logic.

---

# 5. Observable and Histogram

Primary observable: m_yy

- range: 100–160 GeV
- bin width: 1 GeV
- uncertainty: sqrt(N)

---

# 6. Inference (Strict Baseline)

Perform a fit with:

- signal: Gaussian
- background: polynomial (order 4)
- fit range: 100–160 GeV
- use weighting consistent with sqrt(N) uncertainties

Do NOT change model family or configuration.

---

# 7. Required Outputs

Your final output will be reveiwed by the benchmark agent program, thus any wrong output format will cause parseing error.
Do NOT skip any fields.
Your final output shold be in JSON format.

Exaxmple template:
{
  "status": "ok",
  "artifacts": {
    "diphoton_mass_spectrum.json": {
      "bin_edges": [...],
      "bin_counts": [...],
      "bin_uncertainties": [...]
    },
    "diphoton_fit_summary.json": {
      "signal_model_family": "...",
      "background_model_family": "...",
      "fit_range": [...],
      "signal_peak_position": ...
    },
    "data_minus_background.json": {
      "bin_centers": [...],
      "residual_counts": [...],
      "residual_uncertainties": [...]
    },
    "interpretation.md": "...",
    "submission_trace.json": {
      "task_id": task_id,
      "workflow_stages": [
        {"stage_id": "data_loading", "order_index": 1, "status": "ok", "depends_on": []},
        ...
      ],
      "baseline_assumptions_used": [
        "...",
      ],
      "object_definition": {
        "type": "...",
        "multiplicity": 2,
        "ordering_principle": "...",
        "baseline_assumption": {
            "leading_photon_index": ...,
            "subleading_photon_index": ...
        }
      },
      "cuts_applied": [
        {"cut_id": "...", "applies_to": "...", "variable": "...", "operator": "...", "value": ..., "applied": True},
        ...
      ],
      "derived_observables": [
        {"name": "...", "depends_on": ["..."]},
        ...
      ],
      "observable_constructed": {
        "name": "...",
        "inputs": ["..."],
        "formula_summary": "..."
      },
      "primary_observable": {
        "name": "...",
        "inputs": ["..."],
        "construction": "..."
      },
      "histogram_definition": {
        "observable": "...",
        "range": [...],
        "bin_width": ...,
        "uncertainty_model": "..."
      },
      "fit_model_family_used": {
        "signal": "...",
        "background": "...",
        "background_order": ...,
        "fit_range_GeV": [...],
        "weighting_scheme": "..."
      },
      "output_files_generated": [
        "...",
      ],
      "reported_result": {
        "signal_peak_position": 125.1
      }
    }
  }
}

---

# 8. Anti-Cheating Requirement

All outputs MUST be derived from actual computation.

Do NOT fabricate results or skip required steps.

---

# 9. Interpretation Requirement

Write a short conclusion:

- whether a Higgs-like excess is observed
- approximate peak position

The conclusion must be consistent with the fit and residual results.

---

# 10. Runtime Input Rules

If `shared_input_dir` is provided, treat it as read-only input.
Do not modify dataset files in place.
Return outputs through `submission_bundle_v1` as small structured artifacts only.

