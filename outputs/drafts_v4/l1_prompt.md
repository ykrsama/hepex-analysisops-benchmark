# L1 Task: Rediscover the Higgs boson in \(H \rightarrow \gamma\gamma\)

## Objective
Run the specified diphoton analysis on ATLAS Open Data and produce machine-readable outputs that document the workflow, event selection, histogram, and fit result.

The goal is to identify a diphoton mass peak near 125 GeV using a binned fit.

## Dataset
Use ATLAS Open Data release `2025e-13tev-beta`, skimmed dataset `GamGam`, data only.

Combine all of these periods into one analysis sample:

- `2015D`
- `2015E`
- `2015F`
- `2015G`
- `2015H`
- `2015J`
- `2016A`
- `2016B`
- `2016C`
- `2016D`
- `2016E`
- `2016F`
- `2016G`
- `2016K`
- `2016L`

## Required workflow
Execute these stages in this order and record them exactly in `submission_trace.json`:

1. `load_data`
2. `select_photons`
3. `reconstruct_mass`
4. `apply_pt_over_mass`
5. `concatenate_selected_masses`
6. `histogram_mass`
7. `fit_mass_spectrum`

## Event selection
Define leading and subleading photons by descending `photon_pt`.

Apply these requirements:

- both photons pass tight ID
- leading photon `pT > 50 GeV`
- subleading photon `pT > 30 GeV`
- relative isolation for each photon: `photon_ptcone20 / photon_pt < 0.055`
- veto `1.37 < |eta| < 1.52` for both photons
- reconstruct diphoton invariant mass
- require `m_gg != 0`
- after mass reconstruction, require:
  - leading `pT / m_gg > 0.35`
  - subleading `pT / m_gg > 0.35`

## Mass reconstruction
Use the two-photon four-momentum sum.

For `submission_trace.json`, record these exact strings:

- `px_definition`: `pt*cos(phi)`
- `py_definition`: `pt*sin(phi)`
- `pz_definition`: `pt*sinh(eta)`
- `formula`: `sqrt(E_tot^2-px_tot^2-py_tot^2-pz_tot^2)`

Inputs must include:

- `photon_pt`
- `photon_eta`
- `photon_phi`
- `photon_e`

## Histogram
Build the diphoton mass histogram with:

- observable: `m_gg`
- range: `100` to `160` GeV
- bin width: `1` GeV
- number of bins: `60`
- per-bin statistical uncertainty: `sqrt(N)`

## Fit
Perform a binned fit over `100` to `160` GeV using:

- signal model: Gaussian
- background model: 4th-order polynomial
- fit weighting: inverse variance from the bin uncertainties

Initial signal guess should be near:

- `mu ≈ 125 GeV`
- `sigma ≈ 2 GeV`

## Required output files
Write these files in the working directory:

1. `submission_trace.json`
2. `mass_histogram.json`
3. `fit_result.json`
4. `reasoning_summary.md`

## Required JSON content

### 1) `submission_trace.json`
Use this structure and field names:

```json
{
  "dataset": {
    "release": "2025e-13tev-beta",
    "stream": "GamGam",
    "mode": "data_only",
    "periods": ["2015D","2015E","2015F","2015G","2015H","2015J","2016A","2016B","2016C","2016D","2016E","2016F","2016G","2016K","2016L"]
  },
  "pipeline_stages": ["load_data","select_photons","reconstruct_mass","apply_pt_over_mass","concatenate_selected_masses","histogram_mass","fit_mass_spectrum"],
  "photon_ordering": "descending_pt",
  "cuts": {
    "tight_id_both": true,
    "leading_pt_min_gev": 50.0,
    "subleading_pt_min_gev": 30.0,
    "relative_isolation_max": 0.055,
    "eta_transition_veto_abs_eta_window": [1.37, 1.52],
    "mass_nonzero_required": true,
    "leading_pt_over_mgg_min": 0.35,
    "subleading_pt_over_mgg_min": 0.35
  },
  "mass_reconstruction": {
    "inputs": ["photon_pt", "photon_eta", "photon_phi", "photon_e"],
    "px_definition": "pt*cos(phi)",
    "py_definition": "pt*sin(phi)",
    "pz_definition": "pt*sinh(eta)",
    "formula": "sqrt(E_tot^2-px_tot^2-py_tot^2-pz_tot^2)"
  },
  "histogram": {
    "observable": "m_gg",
    "range_gev": [100.0, 160.0],
    "bin_width_gev": 1.0,
    "n_bins": 60,
    "uncertainty": "sqrtN"
  },
  "fit_model": {
    "signal": "gaussian",
    "background": "polynomial",
    "background_order": 4,
    "fit_range_gev": [100.0, 160.0],
    "weighting": "inverse_variance"
  },
  "cutflow": {
    "input_events": 0,
    "after_tight_id": 0,
    "after_pt": 0,
    "after_isolation": 0,
    "after_eta_veto": 0,
    "after_mass_nonzero": 0,
    "after_pt_over_mass": 0,
    "selected_events": 0
  },
  "metadata": {
    "status": "success"
  }
}
```

Populate the integer counts with actual values.

### 2) `mass_histogram.json`
Use this structure:

```json
{
  "range_gev": [100.0, 160.0],
  "bin_width_gev": 1.0,
  "bin_edges_gev": [],
  "counts": [],
  "uncertainties": []
}
```

Requirements:

- `bin_edges_gev` length = `61`
- `counts` length = `60`
- `uncertainties` length = `60`

### 3) `fit_result.json`
Use this structure:

```json
{
  "status": "success",
  "model": {
    "signal": "gaussian",
    "background": "polynomial",
    "background_order": 4
  },
  "fit_range_gev": [100.0, 160.0],
  "mu": 125.0,
  "sigma": 2.0,
  "signal_yield": 0.0,
  "chi2_ndf": 0.0
}
```

Populate numeric values from your fit.

## Required reasoning file
### 4) `reasoning_summary.md`
Write a short explanation covering:

- why tight ID and isolation are used
- why the eta transition region is vetoed
- why `m_gg` must be reconstructed before the `pT/m_gg` cut
- why a Gaussian + smooth polynomial model is appropriate

Keep it short and concrete.

## Notes
- Use data only.
- Combine all listed periods.
- Do not change the cut thresholds, histogram range, or fit model.
- If you need a fit-stability treatment for zero-count bins, you may regularize the fit internally, but keep the recorded histogram uncertainties as `sqrt(N)` in `mass_histogram.json`.
