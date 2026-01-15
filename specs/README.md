# Specs

```
specs/<task_name>/
  task_spec.yaml        # execution & environment contract
  rubric.yaml           # scoring rules (gates / rule_checks / llm_checks)
  eval_ref.yaml         # evaluation reference (optional)
  white_prompt.md       # task instruction to white agent (optional but recommended)
  judge_prompt.md       # LLM judge prompt (only if llm_checks exist)

```

