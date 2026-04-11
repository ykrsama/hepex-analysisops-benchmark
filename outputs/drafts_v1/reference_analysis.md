# Objective
Rediscover the Higgs boson in proton–proton collisions at 13 TeV through the H → γγ decay by identifying a localized excess in the diphoton invariant-mass spectrum near 125 GeV.

# Data
- ATLAS Open Data, 13 TeV (release: 2025e-13tev-beta)
- Data samples: inclusive “data” group, “GamGam” skim (events with at least two photon candidates)
- Periods used: 2015 (D, E, F, G, H, J) and 2016 (A, B, C, D, E, F, G, K, L)
- Total integrated luminosity: approximately 36.1 fb⁻¹
- Event tree: analysis ntuples containing photon kinematics and identification/isolation variables

# Key Variables
- photon_pt: photon transverse momentum
- photon_eta: photon pseudorapidity
- photon_phi: photon azimuthal angle
- photon_e: photon energy
- photon_isTightID: photon identification flag (Tight)
- photon_ptcone20: isolation variable (scalar pT in a cone around the photon)
- Derived:
  - m_γγ: diphoton invariant mass from the sum of the two leading photon four-momenta built from (pt, eta, phi, E)
  - Relative photon momenta: pT(γ_i)/m_γγ for i = 1, 2 (leading, subleading)

# Selection
- Photon identification:
  - Both leading photons must pass Tight ID (photon_isTightID = True for each)
- Kinematics:
  - Leading photon pT > 50 GeV
  - Subleading photon pT > 30 GeV
- Isolation:
  - For each photon, photon_ptcone20 / photon_pt < 0.055
- Geometric acceptance:
  - Exclude the calorimeter barrel–endcap transition: veto 1.37 < |η| < 1.52 for each photon
- Diphoton topology:
  - Compute m_γγ from the two leading photons; require m_γγ > 0
  - Symmetry/energy scale: pT(γ1)/m_γγ > 0.35 and pT(γ2)/m_γγ > 0.35

# Observable
- Diphoton invariant-mass distribution m_γγ
- Typical analysis window: 100–160 GeV with O(1 GeV) binning
- Per-bin statistical uncertainty: √N

# Analysis
- Read all diphoton-skimmed data files for the listed periods
- For each event:
  - Select the two leading photons
  - Apply the identification, kinematic, isolation, and η-region veto cuts
  - Build photon four-momenta from (pt, eta, phi, E) and compute m_γγ
- Aggregate the selected m_γγ values across all files
- Histogram m_γγ in the analysis window with statistical uncertainties

# Inference
- Perform a binned fit to the m_γγ histogram with:
  - Background model: 4th-order polynomial
  - Signal model: Gaussian (detector mass resolution)
  - Fit via weighted least squares using per-bin statistical uncertainties
- Extract:
  - Signal peak position (Gaussian mean), expected near 125 GeV
  - Signal width (Gaussian sigma), representing mass resolution
  - Signal yield (Gaussian amplitude)
- Validate by comparing the fitted signal+background curve to data and by inspecting the background-subtracted spectrum

# Interpretation
- A localized excess near 125 GeV in the diphoton invariant-mass spectrum is observed, consistent with H → γγ
- The result demonstrates the Higgs boson signature in inclusive ATLAS Open Data using simple, robust selections and a standard signal+background fit
- This constitutes a rediscovery-style benchmark rather than a precision measurement (systematic uncertainties and detailed production-mode separation are not treated)
