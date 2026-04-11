# Task: Rediscover the Higgs boson in \(H \rightarrow \gamma\gamma\)

Use the ATLAS Open Data release `2025e-13tev-beta` and the skimmed **data-only** dataset `GamGam` to reconstruct the diphoton invariant-mass spectrum and show the Higgs excess near 125 GeV.

## Data scope
Process and combine all available `GamGam` data files for these periods:

- 2015: D, E, F, G, H, J
- 2016: A, B, C, D, E, F, G, K, L

If your code discovers all `GamGam` data files programmatically under the release and processes them all, that is acceptable.

## Required branches
Use the photon branches needed for selection and mass reconstruction:

- `photon_pt`
- `photon_eta`
- `photon_phi`
- `photon_e`
- `photon_isTightID`
- `photon_ptcone20`

Assume each event has at least two photon candidates in this skim.

## Event selection
Apply the following selection to the two photons used in the diphoton pair:

1. Both photons must pass tight ID:
   - `photon_isTightID[0] == True`
   - `photon_isTightID[1] == True`

2. Ordered photon \(p_T\) cuts:
   - leading photon \(p_T > 50\) GeV
   - subleading photon \(p_T > 30\) GeV

3. Relative isolation for each photon:
   - `photon_ptcone20 / photon_pt < 0.055`

4. Veto the calorimeter barrel/end-cap transition region for both photons:
   - reject photons with \(1.37 < |\eta| < 1.52\)

5. Reconstruct the diphoton invariant mass \(m_{\gamma\gamma}\) from the two photon four-momenta using `photon_pt`, `photon_eta`, `photon_phi`, and `photon_e`.

6. Reject events with null diphoton mass:
   - \(m_{\gamma\gamma} \neq 0\)

7. After computing \(m_{\gamma\gamma}\), apply:
   - leading photon \(p_T / m_{\gamma\gamma} > 0.35\)
   - subleading photon \(p_T / m_{\gamma\gamma} > 0.35\)

## Observable and histogram
Build the selected diphoton invariant-mass distribution:

- observable: \(m_{\gamma\gamma}\)
- histogram range: 100 to 160 GeV
- bin width: 1 GeV
- statistical uncertainty per bin: \(\sqrt{N}\)

Concatenate selected events from all periods into one combined sample before making the final histogram.

## Fit
Fit the binned diphoton mass histogram over 100–160 GeV with:

- **signal**: Gaussian
- **background**: 4th-order polynomial

Use reasonable initial signal guesses near:

- mean \(= 125\) GeV
- width \(\sigma \approx 2\) GeV

Use the bin uncertainties to weight the fit (inverse-uncertainty or inverse-variance weighting is fine if implemented consistently).

## Deliverables
Produce:

1. Code that performs the full workflow.
2. A plot of the diphoton mass spectrum with data points and the fit.
3. A background-only component or comparison that makes the excess near 125 GeV visible.
4. A brief summary reporting at least:
   - the fitted Gaussian mean
   - the fitted Gaussian width
   - a short statement on whether a localized excess near 125 GeV is seen

You may use any reasonable Python/HEP libraries. Exact plotting style is not important; the physics workflow and result are.
