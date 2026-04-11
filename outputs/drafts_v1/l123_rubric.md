## L1_prompt
Task: Rediscover the Higgs boson in ATLAS Open Data via H → γγ by identifying a localized excess near 125 GeV in the diphoton invariant-mass spectrum. Follow the steps below.

Data
- Use ATLAS Open Data 13 TeV, release 2025e-13tev-beta.
- Read all “GamGam” skim files for periods:
  - 2015: D, E, F, G, H, J
  - 2016: A, B, C, D, E, F, G, K, L
- Process all files; merge results across periods.

Event selection (per event)
1) Photon candidates and ordering:
   - Select photon candidates from the event tree.
   - Order photons by transverse momentum pt; take the two leading photons (γ1 = leading, γ2 = subleading).
2) Identification:
   - Require both photons satisfy Tight ID: photon_isTightID == True.
3) Kinematics:
   - Require pt(γ1) > 50 GeV and pt(γ2) > 30 GeV.
4) Isolation:
   - For each photon, require photon_ptcone20 / photon_pt < 0.055.
5) Geometric acceptance:
   - For each photon, veto the barrel–endcap transition: exclude 1.37 < |η| < 1.52.
6) Diphoton mass and topology:
   - Build each photon four-vector from (pt, eta, phi, E).
   - Compute the diphoton invariant mass m_γγ from the sum of the two four-vectors; require m_γγ > 0.
   - Require pT(γ1)/m_γγ > 0.35 and pT(γ2)/m_γγ > 0.35.

Observable and histogramming
- Observable: m_γγ of selected events.
- Histogram m_γγ in the window 100–160 GeV with 1 GeV bin width.
- Per-bin statistical uncertainty: σ_i = sqrt(N_i). Handle empty bins safely (e.g., treat σ_i = 1 for N_i = 0 in the fit weights).

Signal+background fit
- Model:
  - Background: 4th-order polynomial in m_γγ.
  - Signal: Gaussian peak.
  - Total model: polynomial + Gaussian.
- Fit using weighted least squares with weights 1/σ_i^2.
- Initialize Gaussian mean near 125 GeV and width O(1–3 GeV).
- Extract:
  - Gaussian mean (mass peak position)
  - Gaussian sigma (mass resolution)
  - Gaussian amplitude; also report the integral signal yield = amplitude × sqrt(2π) × sigma.

Validation and outputs
- Plots:
  - Data histogram with error bars; overlay best-fit signal+background curve and background-only component.
  - Background-subtracted spectrum (data − fitted background) with the fitted Gaussian overlaid.
  - Residuals or pulls vs. mass.
- Numerical outputs:
  - Best-fit parameters with uncertainties (mean, sigma, amplitude; polynomial coefficients).
  - Goodness-of-fit metrics (χ²/ndf).
  - Simple local significance estimate around the peak (e.g., S/√B in a small mass window using the fitted background).
- Save:
  - Plots as PNG/PDF.
  - Fit results as JSON/YAML.
  - The m_γγ histogram (e.g., as CSV or ROOT/Parquet).

Deliverable
- A self-contained script/notebook that:
  - Loads the specified data, applies the exact selection above, constructs m_γγ, produces the histogram, fits the model, and saves plots and results.
  - Is reproducible and runs end-to-end without manual intervention.


## L2_prompt
Goal: Using ATLAS Open Data (13 TeV, release 2025e-13tev-beta), rediscover the Higgs boson through H → γγ in about 36.1 fb⁻¹ by finding a narrow resonance near 125 GeV in the diphoton invariant-mass spectrum.

Guidance
- Data: Use the “GamGam” skim from 2015–2016 periods (2015 D–J; 2016 A–L as available). Merge all periods.
- Event selection: Build a robust diphoton selection for prompt, isolated photons in the central detector acceptance. Include:
  - Tight photon identification for both photons.
  - Isolation using ptcone20 relative to photon pt.
  - Central |η| acceptance and a veto of the barrel–endcap transition region.
  - Kinematic thresholds appropriate for Higgs-like diphoton events; relative pT thresholds pT(γ_i)/m_γγ around 0.35 are standard.
  - Use the two leading photons per event.
- Observable: Construct m_γγ from photon four-vectors built from (pt, eta, phi, E).
- Histogram: Choose an analysis window around the expected signal (e.g., 100–160 GeV) with O(1 GeV) binning and Poisson uncertainties.
- Inference: Fit the m_γγ spectrum with a smooth background model and a narrow resonance model for the signal (e.g., Gaussian-like). Use a weighted fit with per-bin statistical uncertainties.
- Extract: Peak position, width (mass resolution), and signal yield. Provide uncertainties.
- Validation: Overlay the fit on the data, show a background-subtracted spectrum, and provide a simple significance or goodness-of-fit assessment.
- Outputs: Save plots and a machine-readable summary of the fit parameters and metrics. Provide a script/notebook that runs end-to-end.


## L3_prompt
Objective: Using ATLAS Open Data at 13 TeV (≈36 fb⁻¹, 2015–2016), demonstrate the Higgs boson in the diphoton final state by showing a localized excess near 125 GeV in the data.

Requirements
- Use the “GamGam” diphoton-skimmed data from the 2025e-13tev-beta release (2015–2016 periods). Combine all available periods.
- Design the full analysis: event selection, observable definition, statistical model, and inference procedure. You may use only data-driven background modeling.
- Deliver:
  - A reproducible pipeline that runs end-to-end and outputs plots and a machine-readable summary of your fit results.
  - Figures that clearly demonstrate the excess and an accompanying brief justification of your modeling and selection choices.
  - Quantitative estimates of the signal peak position, width, and yield with uncertainties, plus at least one basic validation or stress test of your result.

No further method hints are provided; choose reasonable, defensible approaches consistent with standard diphoton Higgs searches.


## rubric
public:
  - dimension: execution
    description: The analysis runs end-to-end and produces the required plots and fit outputs without errors.
  - dimension: pipeline
    description: The workflow includes appropriate stages: data loading, diphoton selection, mγγ construction, histogramming, fitting, and reporting.
  - dimension: reasoning
    description: Scientific choices (selection, modeling, fit window/binning) are motivated and consistent with an H → γγ search.
  - dimension: implementation
    description: Core computations are correct (photon ordering, selection logic, mγγ calculation, uncertainty handling, weighted fitting).
  - dimension: analysis
    description: A clear diphoton excess is extracted; peak position, width, and yield are reported with uncertainties and a goodness-of-fit metric.
  - dimension: validation
    description: The result is checked (e.g., comparisons to background-only, residuals/pulls, alternative binning/window) and found to be stable.

private:
  execution:
    - Code completes without uncaught exceptions on the full 2015–201
