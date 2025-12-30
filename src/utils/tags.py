import re
from typing import Dict

def extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"Missing <{tag}>...</{tag}> block")
    return m.group(1).strip()

def parse_request_tags(text: str) -> Dict[str, str]:
    return {
        "white_agent_url": extract_tag(text, "white_agent_url"),
        "env_config": extract_tag(text, "env_config"),
    }

def parse_action_tag(text: str) -> str:
    # white agent must respond with exactly one <json>...</json>
    return extract_tag(text, "json")
