# 1. Objective

Rediscover the Higgs boson in the diphoton channel by reconstructing the diphoton invariant-mass spectrum (m_γγ) and testing for a localized Higgs-like excess near 125 GeV.

---

# 2. Dataset

Use ATLAS Open Data:

- Release: 2025e-13tev-beta
- Sample: GamGam
- Mode: diphoton_skim

Combine all specified 2015–2016 periods into a single spectrum.

---

# 3. Submission Contract Requirement

Before producing any outputs, you MUST read the submission contract carefully.

The submission contract is the authoritative specification for:
- required filenames
- required fields
- field naming
- output completeness

Do NOT invent alternative output formats.

This prompt defines scientific behavior only.

---

# 4. Required Workflow (Strict L1 Execution)

Reproduce the baseline workflow exactly in this order:

1. data_loading  
2. event_selection  
3. diphoton_mass_construction  
4. spectrum_histogramming  
5. uncertainty_assignment  
6. spectrum_fitting  
7. signal_interpretation  

Do NOT reorder, skip, or redesign stages.

---

# 5. Event/Object Selection (Exact Baseline)

Use the leading and subleading photons.

Baseline assumption:
- photon indices 0 and 1 correspond to the ordered leading/subleading pair in this dataset

Do NOT search for alternative pairings.

Apply ALL cuts exactly:

- photon_count >= 2
- leading photon tight ID == true
- subleading photon tight ID == true
- leading photon pt > 50 GeV
- subleading photon pt > 30 GeV
- isolation ratio < 0.055
- eta transition veto [1.37, 1.52]
- m_yy != 0
- pt / m_yy > 0.35 (both photons)

Do NOT modify thresholds or logic.

---

# 6. Observable and Histogram

Primary observable: m_yy

- range: 100–160 GeV
- bin width: 1 GeV
- uncertainty: sqrt(N)

---

# 7. Inference (Strict Baseline)

Perform a fit with:

- signal: Gaussian
- background: polynomial (order 4)
- fit range: 100–160 GeV
- use weighting consistent with sqrt(N) uncertainties

Do NOT change model family or configuration.

---

# 8. Required Outputs

- diphoton_mass_spectrum.json
- diphoton_fit_summary.json
- data_minus_background.json
- interpretation.md
- submission_trace.json

---

# 9. Execution Trace Requirement (CRITICAL)

submission_trace.json is REQUIRED.

It must be STRUCTURED (not narrative).

It must include:

- workflow_stages (ordered execution)
- cuts_applied (with explicit values)
- observable_constructed
- fit_model_family_used
- output_files_generated
- reported_result (including signal_peak_position)

Do NOT use free-form text as the main structure.

---

# 10. Anti-Cheating Requirement

All outputs MUST be derived from actual computation.

Do NOT fabricate results or skip required steps.

---

# 11. Interpretation Requirement

Write a short conclusion:

- whether a Higgs-like excess is observed
- approximate peak position

The conclusion must be consistent with the fit and residual results.

---

# 12. Runtime Input Rules

If `shared_input_dir` is provided, treat it as read-only input.
Do not modify dataset files in place.
Return outputs through `submission_bundle_v1` as small structured artifacts only.
