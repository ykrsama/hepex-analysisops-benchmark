# src/engine/llm_judge_gemini.py
from __future__ import annotations
import os
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from google import genai
from google.genai import types  # google-genai 

from .prompt_render import render_judge_prompt


@dataclass
class LLMJudgeResult:
    ok: bool
    raw_text: str
    parsed: Optional[Dict[str, Any]]
    error: str


class GeminiJudge:
    """
    Minimal Gemini judge.
    Env:
      - GEMINI_API_KEY  (Gemini Developer API)
      - HEPEX_GEMINI_MODEL (optional) e.g. "gemini-2.0-flash"
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = model or os.getenv("HEPEX_GEMINI_MODEL", "gemini-2.0-flash")

    def judge(self, spec: Dict[str, Any], trace: Dict[str, Any], rule_signals: Dict[str, Any], rule_issues: list[dict[str, Any]]) -> LLMJudgeResult:
        rubric = spec["rubric"]
        wf = spec.get("workflow_ref", {}) or {}

        template = spec["judge_prompt"]  # already loaded text
        prompt = render_judge_prompt(
            template,
            rubric=rubric,
            workflow_ref=wf,
            trace=trace,
            rule_signals=rule_signals,
            rule_issues=rule_issues,
        )

        # Try JSON mode (best effort). If provider rejects, we still parse from text.
        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            text = (resp.text or "").strip()
        except Exception as e:
            # fallback: no mime type, still ask prompt to return JSON
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.0),
                )
                text = (resp.text or "").strip()
            except Exception as e2:
                return LLMJudgeResult(False, "", None, f"Gemini call failed: {type(e2).__name__}: {e2}")

        # parse JSON
        try:
            obj = json.loads(text)
            if not isinstance(obj, dict):
                return LLMJudgeResult(False, text, None, "LLM output is not a JSON object")
            return LLMJudgeResult(True, text, obj, "")
        except Exception as e:
            return LLMJudgeResult(False, text, None, f"JSON parse failed: {type(e).__name__}: {e}")
