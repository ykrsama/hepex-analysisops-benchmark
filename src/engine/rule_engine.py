# src/engine/rule_engine.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .checks import REGISTRY, CheckResult

@dataclass
class RuleReport:
    gate_passed: bool
    gate_failures: List[str]
    rule_score: float
    rule_max: float
    issues: List[Dict[str, Any]]
    signals: Dict[str, Any]


def evaluate_rules(spec: Dict[str, Any], trace: Dict[str, Any]) -> RuleReport:
    rubric = spec["rubric"]
    wf = spec.get("workflow_ref", {}) or {}
    total_max = float(rubric.get("total", 100))

    issues: List[Dict[str, Any]] = []
    signals: Dict[str, Any] = {}

    # ---- gates ----
    gate_failures: List[str] = []
    for g in rubric.get("gates", []) or []:
        ctype = g.get("type")
        fn = REGISTRY.get(ctype)
        if fn is None:
            gate_failures.append(f"unknown_gate_type:{ctype}")
            continue
        g2 = dict(g)
        g2["gate"] = True
        res: CheckResult = fn(g2, trace, rubric, wf)
        issues.extend(res.issues)
        signals.update(res.signals)
        if res.passed is False:
            gate_failures.append(g.get("id", ctype))

    if gate_failures:
        return RuleReport(
            gate_passed=False,
            gate_failures=gate_failures,
            rule_score=0.0,
            rule_max=total_max,
            issues=issues,
            signals=signals,
        )

    # ---- rule checks ----
    score = 0.0
    max_score = 0.0
    for rc in rubric.get("rule_checks", []) or []:
        ctype = rc.get("type")
        fn = REGISTRY.get(ctype)
        if fn is None:
            issues.append({"severity":"error","code":"UNKNOWN_CHECK_TYPE","message":f"Unknown rule check type: {ctype}"})
            continue
        res: CheckResult = fn(rc, trace, rubric, wf)
        score += float(res.points)
        max_score += float(res.max_points)
        issues.extend(res.issues)
        signals.update(res.signals)

    # 规则分如果没凑到 total，可以不强行缩放；也可以选择缩放到 total（看你偏好）
    return RuleReport(True, [], score, total_max, issues, signals)
