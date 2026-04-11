Goal: Rediscover the Higgs boson in the \(H \rightarrow \gamma\gamma\) channel using the provided ATLAS Open Data skimmed diphoton sample.

Complete the following tasks:

1. Read all provided diphoton data files and combine them into one analysis sample. Process file-by-file or in chunks if needed.
2. For each event, require at least two reconstructed photon candidates and use the two highest-\(p_T\) photons as the diphoton candidate.
3. Apply a standard diphoton Higgs selection:
   - both photons pass a tight photon-identification requirement;
   - both photons are within detector acceptance and outside the barrel-endcap transition region;
   - the leading photon is harder than the subleading photon and both satisfy asymmetric \(p_T\) thresholds;
   - both photons satisfy an isolation requirement;
   - reject events with invalid diphoton reconstruction.
4. Reconstruct the diphoton invariant mass \(m_{\gamma\gamma}\) from the selected photon four-momenta.
5. Apply a diphoton-level balance requirement using the photon \(p_T / m_{\gamma\gamma}\) fractions for both photons.
6. Build a histogram of \(m_{\gamma\gamma}\) in a Higgs-sensitive mass window that includes the region near 125 GeV.
7. Fit the mass spectrum with:
   - a smooth background component;
   - a narrow signal component centered near the Higgs region.
8. Produce the following outputs:
   - a plot of the diphoton invariant-mass spectrum with the fit overlaid;
   - the total number of selected diphoton candidates;
   - the fitted peak position and a signal-yield or signal-strength proxy;
   - a brief conclusion stating whether a localized excess near 125 GeV is visible.

Notes:
- Use the data sample only; no simulated signal is required.
- If branch names differ from your expectations, use the equivalent photon kinematic, ID, and isolation variables present in the dataset.
- Keep the workflow reproducible and runnable end-to-end.
