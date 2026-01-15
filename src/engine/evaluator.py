# src/engine/evaluator.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from .rule_engine import evaluate_rules, RuleReport
from .llm_judge_gemini import GeminiJudge
from .checks import clamp  # 或者你放到 utils.py


def evaluate_task(spec: Dict[str, Any], trace: Dict[str, Any], *, gemini: Optional[GeminiJudge] = None) -> Dict[str, Any]:
    rubric = spec["rubric"]
    total_max = float(rubric.get("total", 100))

    # 1) deterministic rules
    rule: RuleReport = evaluate_rules(spec, trace)

    if not rule.gate_passed:
        # gate fail: by design → 0 (或你支持 fail_total_score)
        return {
            "status": "fail",
            "hard_checks_passed": False,
            "hard_failures": rule.gate_failures,
            "final": {"total_score": 0.0, "max_score": total_max, "normalized_score": 0.0},
            "rule": {"score": 0.0},
            "llm": {"score": 0.0},
            "issues": rule.issues,
            "signals": rule.signals,
        }

    # 2) LLM checks (optional)
    llm_score = 0.0
    llm_meta: Dict[str, Any] = {}
    llm_issues: List[dict] = []

    llm_checks = rubric.get("llm_checks", []) or []
    if llm_checks and gemini is not None:
        # v0: assume only one reasoning check; can loop later
        for lc in llm_checks:
            if lc.get("type") != "llm_reasoning":
                llm_issues.append({"severity":"error","code":"UNKNOWN_LLM_CHECK","message":f"Unknown llm check type: {lc.get('type')}"})
                continue

            cap = float(lc.get("points", 0.0))
            out_key = lc.get("output_key", "dimension_scores.method_reasoning")
            clamp_rng = lc.get("clamp", [0, 100])
            conf_key = lc.get("confidence_key", None)

            res = gemini.judge(spec, trace, rule.signals, rule.issues)
            if not res.ok or not res.parsed:
                llm_issues.append({"severity":"warn","code":"LLM_FAIL","message":res.error, "evidence":res.raw_text[:400]})
                continue

            obj = res.parsed
            # read output_key: simple dotted path
            from .checks import get_path
            raw = get_path(obj, out_key, None)
            if not isinstance(raw, (int, float)):
                llm_issues.append({"severity":"warn","code":"LLM_MISSING_SCORE","message":f"Missing {out_key}", "evidence":res.raw_text[:400]})
                continue

            raw = float(raw)
            raw = clamp(raw, float(clamp_rng[0]), float(clamp_rng[1]))  # 0-100
            conf = 1.0
            if conf_key and isinstance(obj.get(conf_key), (int, float)):
                conf = clamp(float(obj[conf_key]), 0.0, 1.0)

            contrib = (raw / 100.0) * cap * conf
            contrib = clamp(contrib, 0.0, cap)

            llm_score += contrib
            llm_meta[lc.get("id","method_reasoning")] = {
                "raw": raw, 
                "confidence": conf, 
                "cap": cap, 
                "contrib": contrib,
                "explanation": obj.get("explanation", "")
            }

            notes = obj.get("notes", [])
            if isinstance(notes, list):
                llm_issues.extend([n for n in notes if isinstance(n, dict)])

    # 3) final merge
    # Calculate LLM max possible score
    llm_max = sum(float(lc.get("points", 0.0)) for lc in llm_checks)

    total_score = float(rule.rule_score) + float(llm_score)
    final_max = float(rule.rule_max) + llm_max
    
    # Do NOT clamp total to a fixed value. It should be capped by final_max naturally if logic is correct.
    total_score = clamp(total_score, 0.0, final_max)

    return {
        "status": "ok",
        "hard_checks_passed": True,
        "hard_failures": [],
        "final": {
            "total_score": total_score, 
            "max_score": final_max, 
            "normalized_score": total_score / max(1e-9, final_max)
        },
        "rule": {"score": rule.rule_score, "max": rule.rule_max},
        "llm": {"score": llm_score, "max": llm_max, "meta": llm_meta},
        "issues": rule.issues + llm_issues,
        "signals": rule.signals,
    }