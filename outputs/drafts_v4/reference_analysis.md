# Objective
Rediscover the Higgs boson in the diphoton decay channel, \(H \rightarrow \gamma\gamma\), by selecting clean two-photon events and identifying an excess near \(m_{\gamma\gamma}\approx 125\) GeV in the diphoton invariant-mass spectrum.

# Data
- ATLAS Open Data, 13 TeV proton-proton collisions, release `2025e-13tev-beta`.
- Use the skimmed dataset `GamGam`, containing events with at least two photon candidates.
- Data files span:
  - 2015 periods: D, E, F, G, H, J
  - 2016 periods: A, B, C, D, E, F, G, K, L
- The analysis is performed on data only, combining all listed periods.

# Key Variables
- `photon_pt`: photon transverse momentum
- `photon_eta`: photon pseudorapidity
- `photon_phi`: photon azimuth
- `photon_e`: photon energy
- `photon_isTightID`: photon tight identification flag
- `photon_ptcone20`: photon isolation quantity used as a relative isolation variable
- Derived variable:
  - `mass` or \(m_{\gamma\gamma}\): invariant mass of the two-photon system

# Selection
- Require both photon candidates to pass tight identification:
  - `photon_isTightID[0] == True`
  - `photon_isTightID[1] == True`
- Require ordered photon transverse momenta:
  - leading photon \(p_T > 50\) GeV
  - subleading photon \(p_T > 30\) GeV
- Require relative isolation for each photon:
  - `photon_ptcone20 / photon_pt < 0.055`
- Veto the calorimeter barrel/end-cap transition region for both photons:
  - reject photons with \(1.37 < |\eta| < 1.52\)
- Build the diphoton invariant mass \(m_{\gamma\gamma}\) from the two photon four-momenta.
- Reject events with null diphoton mass:
  - \(m_{\gamma\gamma} \neq 0\)
- Apply photon \(p_T\) relative to diphoton mass requirement, after computing \(m_{\gamma\gamma}\):
  - leading photon \(p_T / m_{\gamma\gamma} > 0.35\)
  - subleading photon \(p_T / m_{\gamma\gamma} > 0.35\)

# Observable
- Primary observable: diphoton invariant mass
  \[
  m_{\gamma\gamma} = \sqrt{E_{\text{tot}}^2 - \mathbf{p}_{\text{tot}}\cdot \mathbf{p}_{\text{tot}}}
  \]
  computed from the sum of the two photon four-momenta using `photon_pt`, `photon_eta`, `photon_phi`, and `photon_e`.
- Histogram the selected \(m_{\gamma\gamma}\) values in the range:
  - 100 to 160 GeV
  - 1 GeV bin width

# Analysis
- Loop over all `GamGam` data files and read the photon branches needed for selection and mass reconstruction.
- Apply the photon identification, kinematic, isolation, and \(\eta\)-veto requirements event-by-event.
- Reconstruct the diphoton invariant mass for surviving events.
- Apply the \(p_T/m_{\gamma\gamma}\) requirement only after mass reconstruction.
- Concatenate all selected diphoton masses from all periods into a single data sample.
- Fill a binned \(m_{\gamma\gamma}\) histogram over 100–160 GeV.
- Estimate per-bin statistical uncertainties as \(\sqrt{N}\).

# Inference
- Perform a binned fit to the diphoton mass histogram using a combined model:
  - signal: Gaussian
  - background: 4th-order polynomial
- Use initial signal guesses near:
  - center \(= 125\) GeV
  - width \(\sigma \approx 2\) GeV
- Fit over the full histogram range, 100–160 GeV, with weights based on inverse bin uncertainties.
- Extract the background shape from the polynomial component and compare data to background to reveal the excess near 125 GeV.
- The Higgs signal is identified as a localized peak above the smooth background in \(m_{\gamma\gamma}\).

# Interpretation
A statistically visible excess near \(m_{\gamma\gamma}\approx 125\) GeV supports the presence of Higgs boson production followed by decay to two photons. The analysis demonstrates that a narrow resonance can be extracted from a large smooth diphoton background using photon-quality cuts, kinematic selections, and a signal-plus-background fit.
