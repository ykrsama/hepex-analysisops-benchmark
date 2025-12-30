import json
import os
from typing import Dict, Any

def _exists(path: str) -> bool:
    return os.path.exists(path)

def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def score_submission_dir(task: Dict[str, Any], submission_dir: str = ".") -> Dict[str, Any]:
    exp = task["expected_outputs"]
    scoring = task["scoring"]

    fit_path = os.path.join(submission_dir, exp["fit_results"]["path"])
    plot_path = os.path.join(submission_dir, exp["plot"]["path"])

    breakdown: Dict[str, float] = {}
    total_w = 0.0
    score = 0.0

    # ---- artifacts ----
    w_files = float(scoring["artifacts"]["files_exist"]["weight"])
    total_w += w_files
    files_ok = _exists(fit_path) and _exists(plot_path)
    breakdown["files_exist"] = 1.0 if files_ok else 0.0
    score += breakdown["files_exist"] * w_files

    w_plot = float(scoring["artifacts"]["plot_generated"]["weight"])
    total_w += w_plot
    breakdown["plot_generated"] = 1.0 if _exists(plot_path) else 0.0
    score += breakdown["plot_generated"] * w_plot

    # ---- metrics ----
    fit_data = {}
    if _exists(fit_path):
        fit_data = _load_json(fit_path)

    for key, cfg in scoring.get("metrics", {}).items():
        w = float(cfg["weight"])
        tol = float(cfg["tolerance"])
        ref = cfg.get("reference", None)
        total_w += w

        if key not in fit_data:
            breakdown[key] = 0.0
            continue

        try:
            val = float(fit_data[key])
        except Exception:
            breakdown[key] = 0.0
            continue

        if ref is None:
            breakdown[key] = 1.0
        else:
            breakdown[key] = 1.0 if abs(val - float(ref)) <= tol else 0.0

        score += breakdown[key] * w

    if total_w > 0:
        score /= total_w

    return {
        "score": score,
        "breakdown": breakdown,
        "paths": {"fit_results": fit_path, "plot": plot_path},
    }
