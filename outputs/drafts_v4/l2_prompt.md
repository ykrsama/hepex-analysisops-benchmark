# L2 Task: Rediscover the Higgs boson in \(H \rightarrow \gamma\gamma\)

## Objective
Using ATLAS Open Data, perform a **data-only** analysis to rediscover the Higgs boson in the diphoton decay channel by identifying a localized excess near 125 GeV in a diphoton mass spectrum.

This is an **L2 guided-autonomy** task:

- The **physics goal is fixed**
- The **exact workflow is not prescribed**
- You must reconstruct a reasonable analysis strategy from the available data and variables

## Dataset
Use:

- **Release:** `2025e-13tev-beta`
- **Sample:** `GamGam`
- **Collision energy:** 13 TeV
- **Data only:** yes

Combine all listed periods into one analysis sample:

- **2015:** D, E, F, G, H, J
- **2016:** A, B, C, D, E, F, G, K, L

## Available photon-level variables
You may use the skimmed `GamGam` content, including at minimum:

- `photon_pt`
- `photon_eta`
- `photon_phi`
- `photon_e`
- `photon_isTightID`
- `photon_ptcone20`

## Task requirements
Reconstruct a complete analysis that:

1. Uses the `GamGam` data sample across the listed periods
2. Chooses a **reasonable diphoton event selection**
3. Reconstructs a **diphoton observable** suitable for Higgs discovery
4. Builds a binned mass spectrum
5. Performs a quantitative signal-extraction step using a **narrow signal model on top of a smooth background model**
6. Reports whether a signal-like excess compatible with \(H \rightarrow \gamma\gamma\) is observed

## Important flexibility
You are **not** required to reproduce any exact reference cuts.

You **should** choose and document:

- an appropriate observable
- a reasonable photon-quality / kinematic / isolation / acceptance strategy
- a sensible histogram range and binning
- a sensible parametric fit or equivalent quantitative signal-extraction method

The benchmark rewards:

- correct observable choice
- reasonable event selection
- a credible signal-extraction workflow
- recovery of a peak near 125 GeV

## Required output files
You must produce all of the following:

1. `submission_trace.json`
2. `fit_result.json`
3. `analysis_note.md`

---

## Required schema: `submission_trace.json`

Write a machine-readable trace of your workflow with this structure:

```json
{
  "dataset": {
    "release": "2025e-13tev-beta",
    "sample": "GamGam",
    "data_only": true
  },
  "years_used": [2015, 2016],
  "periods_used": ["2015D", "2015E", "2015F", "2015G", "2015H", "2015J", "2016A", "2016B", "2016C", "2016D", "2016E", "2016F", "2016G", "2016K", "2016L"],
  "branches_used": [
    "photon_pt",
    "photon_eta",
    "photon_phi",
    "photon_e",
    "photon_isTightID",
    "photon_ptcone20"
  ],
  "workflow_components": {
    "load_multiple_periods": true,
    "photon_pair_selection": true,
    "quality_selection": true,
    "kinematic_selection": true,
    "mass_reconstruction": true,
    "histogramming": true,
    "background_modeling": true,
    "signal_extraction": true
  },
  "observable": {
    "name": "diphoton_invariant_mass",
    "symbol": "m_gg",
    "inputs": ["photon_pt", "photon_eta", "photon_phi", "photon_e"],
    "construction": "four_momentum_sum"
  },
  "event_selection": {
    "min_photons": 2,
    "uses_identification": true,
    "uses_isolation": true,
    "uses_eta_quality_requirement": true,
    "uses_absolute_pt_requirement": true,
    "uses_mass_scaled_pt_requirement": true,
    "thresholds": {
      "leading_pt_GeV": null,
      "subleading_pt_GeV": null,
      "relative_isolation_max": null,
      "eta_veto": null,
      "leading_pt_over_mgg_min": null,
      "subleading_pt_over_mgg_min": null
    }
  },
  "histogram": {
    "range_GeV": [100.0, 160.0],
    "bin_width_GeV": 1.0,
    "n_bins": 60
  },
  "fit": {
    "performed": true,
    "fit_range_GeV": [100.0, 160.0],
    "signal_model_family": "gaussian",
    "background_model_family": "polynomial",
    "signal_model_detail": "",
    "background_model_detail": ""
  },
  "event_counts": {
    "processed": 0,
    "selected": 0
  },
  "artifacts": {
    "mass_spectrum_plot": "",
    "fit_plot": "",
    "analysis_note": "analysis_note.md"
  }
}
```

### Notes
- You may choose different thresholds than the reference analysis.
- If a field is not applicable, keep the key and use `null` or an empty string where appropriate.
- Keep the boolean flags honest: set them to reflect what your workflow actually used.

---

## Required schema: `fit_result.json`

Write the quantitative result of your signal extraction in this structure:

```json
{
  "observable": "diphoton_invariant_mass",
  "signal_detected": true,
  "peak_mass_GeV": 125.0,
  "peak_width_GeV": 2.0,
  "histogram_range_GeV": [100.0, 160.0],
  "fit_range_GeV": [100.0, 160.0],
  "bin_width_GeV": 1.0,
  "signal_model_family": "gaussian",
  "background_model_family": "polynomial",
  "signal_model_detail": "",
  "background_model_detail": "",
  "signal_yield": 0.0,
  "local_significance_sigma": 0.0,
  "background_only_comparison_performed": true,
  "result_summary": ""
}
```

### Controlled vocabulary
Use one of the following for `signal_model_family`:

- `gaussian`
- `gaussian_like`
- `narrow_resonance`

Use one of the following for `background_model_family`:

- `polynomial`
- `smooth_parametric`
- `exponential_like`
- `powerlaw_like`

---

## Required schema: `analysis_note.md`

Provide a short note that explains:

1. why your chosen observable is appropriate for \(H \rightarrow \gamma\gamma\)
2. why your event selection improves signal visibility
3. why your background model is smooth and your signal model is narrow
4. how your final result supports or does not support a Higgs-like excess near 125 GeV

Keep this concise and focused.

---

## Additional guidance
- Use the **data only** sample; do not rely on MC truth labels
- Combine the listed periods into one final spectrum
- Your analysis does not need to match any exact reference implementation
- The key scientific outcome is a **credible excess near 125 GeV in diphoton invariant mass**

## Deliverables summary
Your final submission must include:

- `submission_trace.json`
- `fit_result.json`
- `analysis_note.md`
