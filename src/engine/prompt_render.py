# src/engine/prompt_render.py
from __future__ import annotations
import json
from typing import Any, Dict, List

def pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)

def render_judge_prompt(template: str,
                        *,
                        rubric: Dict[str, Any],
                        eval_ref: Dict[str, Any],
                        trace: Dict[str, Any],
                        rule_signals: Dict[str, Any],
                        rule_issues: List[Dict[str, Any]]) -> str:
    return (template
            .replace("{{RUBRIC}}", pretty(rubric))
            .replace("{{EVAL_REF}}", pretty(eval_ref))
            .replace("{{WORKFLOW_REF}}", pretty(eval_ref))  # backward compat
            .replace("{{SUBMISSION_TRACE}}", pretty(trace))
            .replace("{{RULE_SIGNALS}}", pretty(rule_signals))
            .replace("{{RULE_ISSUES}}", pretty(rule_issues)))

def _builtin_minimal_prompt(task_id: str, task_type: str) -> str:
    return f"""
You are solving a benchmark task.

Task ID: {task_id}
Task Type: {task_type}

You must return a JSON object named SUBMISSION_TRACE.
This JSON will be used for automated evaluation.

Required rules:
- Output JSON only. No extra text.
- If the task fails, set "status" = "error" and explain briefly.

SUBMISSION_TRACE schema (minimum required fields):
{{
  "task_id": "{task_id}",
  "status": "ok" | "error",
  "result": object,
  "method": object,
  "comments": string
}}

Notes:
- Include in "result" any task outputs you computed.
- Include in "method" a brief description of how you produced the result.
- Missing fields may result in score penalties.
"""

