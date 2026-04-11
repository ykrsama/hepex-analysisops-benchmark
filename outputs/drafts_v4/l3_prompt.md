# L3 Task: Open Scientific Autonomy — Rediscover \(H \rightarrow \gamma\gamma\)

## Objective
Using ATLAS Open Data, rediscover the Higgs boson in the diphoton decay channel by identifying a **localized excess near 125 GeV** in the diphoton invariant-mass spectrum and performing a **reasonable quantitative signal extraction**.

## Data
Use:

- **ATLAS Open Data**
- release: **`2025e-13tev-beta`**
- skimmed dataset: **`GamGam`**
- **data only**
- combine the following periods:

```text
2015D, 2015E, 2015F, 2015G, 2015H, 2015J,
2016A, 2016B, 2016C, 2016D, 2016E, 2016F, 2016G, 2016K, 2016L
```

## Scientific freedom
This is an **open-method** task.

You may choose your own:
- photon/event selection strategy
- diphoton reconstruction details
- histogramming or unbinned workflow
- background model
- signal model
- fitting or bump-hunting procedure
- robustness/validation strategy

Multiple valid approaches are acceptable.

## Minimum scientific requirements
Your workflow must still do all of the following:

1. Use the `GamGam` dataset from the specified release and periods.
2. Build or otherwise analyze the **diphoton invariant mass** observable.
3. Search for a **localized excess near 125 GeV** with sufficient sideband context.
4. Provide a **quantitative signal extraction** near the excess.
5. Perform **at least one validation**, chosen from:
   - `alternative_model`
   - `sideband_check`
   - `robustness_test`

Examples of acceptable validation:
- fitting with an alternative background model
- sideband-only background estimation
- repeating the analysis with different binning, fit range, or selection variations

## Required output files
You must write **both** of the following files in the working directory:

- `submission_trace.json`
- `fit_result.json`

Both files must be valid JSON.

---

## Required schema: `submission_trace.json`

Use this exact top-level structure and key names:

```json
{
  "task": "atlas_hgg_open_autonomy",
  "data_release": "2025e-13tev-beta",
  "dataset": "GamGam",
  "used_periods": [
    "2015D", "2015E", "2015F", "2015G", "2015H", "2015J",
    "2016A", "2016B", "2016C", "2016D", "2016E", "2016F", "2016G", "2016K", "2016L"
  ],
  "analysis_strategy": {
    "selection_description": "short text",
    "mass_reconstruction": "short text",
    "spectrum_construction": "short text",
    "signal_extraction": "short text"
  },
  "workflow_status": {
    "load_data": "done",
    "event_selection": "done",
    "mass_reconstruction": "done",
    "spectrum_construction": "done",
    "signal_extraction": "done",
    "validation": "done"
  },
  "event_flow": {
    "events_total": 0,
    "events_after_selection": 0,
    "diphoton_candidates_used": 0
  },
  "observable": {
    "name": "m_gg",
    "range_GeV": [100.0, 160.0],
    "binning_type": "binned",
    "bin_width_GeV": 1.0
  },
  "validation_summary": {
    "performed": true,
    "types": ["alternative_model"],
    "notes": "short text"
  },
  "artifacts": {
    "fit_result": "fit_result.json"
  }
}
```

### Notes
- `used_periods` must use the exact canonical labels shown above.
- If your method is unbinned, set:
  - `"binning_type": "unbinned"`
  - `"bin_width_GeV": null`
- `range_GeV` should describe the mass range actually analyzed.

---

## Required schema: `fit_result.json`

Use this exact top-level structure and key names:

```json
{
  "observable": "m_gg",
  "analysis_mass_range_GeV": [100.0, 160.0],
  "binning": {
    "type": "binned",
    "bin_width_GeV": 1.0
  },
  "peak_detected": true,
  "peak_position_GeV": 125.0,
  "peak_window_GeV": [122.0, 128.0],
  "signal_extraction_method": "short text",
  "signal_model": "short text",
  "background_model": "short text",
  "estimated_signal_yield": 0.0,
  "estimated_background_under_peak": 0.0,
  "signal_to_background": 0.0,
  "local_significance_sigma": 0.0,
  "width_GeV": 0.0,
  "goodness_metric": "short text",
  "goodness_value": 0.0,
  "localized_excess_near_125": true,
  "validation_supports_signal": true,
  "summary": "short text"
}
```

### Notes
- If your method is unbinned, set:
  - `"binning": {"type": "unbinned", "bin_width_GeV": null}`
- Even if you do not use a parametric fit, you must still provide **best-effort numerical estimates** for:
  - `estimated_signal_yield`
  - `estimated_background_under_peak`
  - `signal_to_background`
  - `local_significance_sigma`
- `peak_window_GeV` should bracket the excess region you identify.
- `width_GeV` may be your fitted width or effective peak width estimate.
- `summary` should briefly state what was found.

## Deliverable expectations
A strong submission will:
- show a clear diphoton-mass analysis
- identify a localized excess near 125 GeV
- extract a plausible signal estimate above smooth background
- include at least one meaningful validation

Optional plots, notebooks, or extra files are allowed, but only the two required JSON files are guaranteed to be evaluated.
