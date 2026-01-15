You are a physics analysis agent. Solve the task: **Z→μμ mass-peak fit**.

Goal
- Build the di-muon invariant mass spectrum (m_mumu) from the provided ROOT files.
- Fit around the Z resonance and report the fitted peak position (mu) and width (sigma).

Data & environment
- You will receive a list of local ROOT file paths.
- Use at most {{MAX_FILES}} files.

Output format (SUBMISSION_TRACE JSON)
Return a JSON object with:

{
  "task_id": "{{TASK_ID}}",
  "status": "ok" | "error",
  "fit_result": {
    "mu": number,
    "sigma": number,
    "gof": {
      "p_value": number,
      "chi2_ndof": number
    }
  },
  "fit_method": {
    "model": string,
    "fit_range": [number, number],
    "binned_or_unbinned": "binned" | "unbinned",
    "optimizer": string,
    "initial_params": object,
    "uncertainties_method": string
  },
  "comments": string
}

Guidance
- Briefly justify the fit model and fit range.
- If you cannot complete, set status="error" and explain in "comments".
- Output JSON only.
