# Objective
Rediscover the Higgs boson in the \(H \rightarrow \gamma\gamma\) decay channel by isolating diphoton candidates in ATLAS Open Data and identifying a narrow resonance in the diphoton invariant-mass spectrum near 125 GeV.

# Data
ATLAS Open Data proton-proton collision data at \(\sqrt{s}=13\) TeV, using the skimmed diphoton sample containing events with at least two photon candidates. The analysis combines multiple 2015 and 2016 data-taking periods, corresponding to an integrated luminosity of about 36 fb\(^{-1}\).

# Key Variables
- Photon transverse momentum \(p_T\)
- Photon pseudorapidity \(\eta\)
- Photon azimuth \(\phi\)
- Photon energy \(E\)
- Photon identification quality flag
- Photon isolation variable
- Diphoton invariant mass \(m_{\gamma\gamma}\)

# Selection
- Start from events with at least two reconstructed photon candidates.
- Require both leading photons to pass tight photon identification.
- Require the leading and subleading photons to satisfy asymmetric \(p_T\) thresholds, with the leading photon harder than the subleading one.
- Require both photons to be isolated using a relative isolation criterion.
- Reject photons in the calorimeter barrel–endcap transition region.
- Reconstruct the diphoton invariant mass from the two photon four-momenta.
- Remove pathological events with invalid or zero reconstructed diphoton mass.
- Require both photons to satisfy a minimum \(p_T/m_{\gamma\gamma}\) fraction to suppress asymmetric background configurations.

# Observable
The primary observable is the diphoton invariant mass,
\[
m_{\gamma\gamma},
\]
computed from the summed four-momentum of the two selected photons. The analysis studies the binned \(m_{\gamma\gamma}\) spectrum over a mass window that includes the expected Higgs signal region.

# Analysis
- Read the skimmed diphoton data sample file by file and process events in chunks.
- For each event, apply the photon identification, kinematic, acceptance, and isolation selections.
- Build the diphoton four-momentum and compute \(m_{\gamma\gamma}\).
- Collect the selected diphoton masses from all data periods into a single sample.
- Fill a histogram of the diphoton invariant mass in a window around the Higgs mass.
- Compare the observed mass spectrum to a model consisting of a smooth continuum background plus a localized signal contribution.

# Inference
Extract the Higgs signal by fitting the binned diphoton mass spectrum with:
- a smooth background component, represented by a low-order polynomial or similar empirical shape;
- a narrow signal component, represented by a Gaussian-like peak centered near the Higgs mass.

The signal is identified through an excess above the smooth background in the \(m_{\gamma\gamma}\) distribution, and the fitted peak position gives the reconstructed Higgs mass scale.

# Interpretation
A localized excess in the diphoton invariant-mass spectrum near 125 GeV supports the presence of Higgs boson production followed by \(H \rightarrow \gamma\gamma\) decay. The analysis demonstrates how a rare signal can be extracted from a large continuum background using photon selection, invariant-mass reconstruction, and signal-plus-background fitting.
