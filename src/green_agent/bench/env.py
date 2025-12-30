import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict

import yaml

from src.utils.tags import parse_action_tag
from src.green_agent.bench.score import score_submission_dir


@dataclass
class Action:
    name: str
    kwargs: Dict[str, Any]


def load_task_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class HEPExEnv:
    def __init__(self, task: Dict[str, Any], runtime_limit_sec: int = 900, data_cache_dir: str = ".cache/atlas_opendata"):
        self.task = task
        self.runtime_limit_sec = runtime_limit_sec
        self.data_cache_dir = data_cache_dir

        self.wiki = task.get("wiki", task.get("description", ""))
        self.tools_info = task.get("tools_info", [])
        proto = task.get("interaction_protocol", {})
        self.respond_action_name = proto.get("respond_action_name", "respond")

        self._t0 = None

    def prepare_inputs(self) -> None:
        # Run benchmark-controlled data acquisition (not via white agent)
        for item in self.task.get("inputs", {}).get("data", []):
            acq = item.get("acquisition")
            if not acq:
                continue
            if acq.get("method") == "fetch_script":
                script = acq["script"]
                env = os.environ.copy()
                env["ATLAS_DATA_CACHE_DIR"] = self.data_cache_dir
                subprocess.check_call(["bash", script], env=env)

    def reset(self) -> Dict[str, Any]:
        self._t0 = time.time()
        self.prepare_inputs()
        obs = "User message: Start by inspecting the repo and running the recommended entrypoint.\n"
        return {"observation": obs, "info": {}}

    def build_task_description(self, obs: str) -> str:
        # tau-bench style first message
        return f"""
{self.wiki}

Here's a list of tools you can use (you can use at most one tool at a time):
{json.dumps(self.tools_info, indent=2)}

Please response in the JSON format. Please wrap the JSON part with <json>...</json> tags.
The JSON should contain:
- "name": the tool call function name, or "{self.respond_action_name}" if you want to respond directly.
- "kwargs": the arguments for the tool call, or {{"content": "your message here"}} if you want to respond directly.

User message: {obs}
""".strip()

    def parse_action(self, white_text: str) -> Action:
        action_json = parse_action_tag(white_text)
        data = json.loads(action_json)
        return Action(name=data["name"], kwargs=data.get("kwargs", {}))

    def _check_timeout(self):
        if self._t0 is None:
            return
        if time.time() - self._t0 > self.runtime_limit_sec:
            raise TimeoutError("Runtime limit exceeded")

    def _outputs_exist(self) -> bool:
        exp = self.task.get("expected_outputs", {})
        need = []
        if "fit_results" in exp:
            need.append(exp["fit_results"]["path"])
        if "plot" in exp:
            need.append(exp["plot"]["path"])
        return all(os.path.exists(p) for p in need)

    def step(self, action: Action) -> Dict[str, Any]:
        self._check_timeout()

        if action.name == "run":
            cmd = action.kwargs["cmd"]
            cwd = action.kwargs.get("cwd", ".")
            timeout = action.kwargs.get("timeout_sec", 120)
            p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
            obs = f"Tool call result:\nexit_code={p.returncode}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}\n"

        elif action.name == "read_file":
            path = action.kwargs["path"]
            with open(path, "r", encoding="utf-8") as f:
                obs = "Tool call result:\n" + f.read() + "\n"

        elif action.name == "write_file":
            path = action.kwargs["path"]
            content = action.kwargs["content"]
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            obs = f"Tool call result:\nWrote {path}\n"

        elif action.name == "list_dir":
            path = action.kwargs.get("path", ".")
            obs = "Tool call result:\n" + "\n".join(sorted(os.listdir(path))) + "\n"

        elif action.name == "file_exists":
            path = action.kwargs["path"]
            obs = f"Tool call result:\n{path} exists: {os.path.exists(path)}\n"

        elif action.name == "hash_file":
            import hashlib
            path = action.kwargs["path"]
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            obs = f"Tool call result:\nsha256={h.hexdigest()}\n"

        elif action.name == self.respond_action_name:
            obs = "User message:\n" + action.kwargs.get("content", "") + "\n"

        else:
            obs = f"Tool call result:\nUnknown tool: {action.name}\n"

        done = self._outputs_exist()
        reward = 1.0 if done else 0.0

        # next message: keep tau-bench convention
        next_green_msg = f"Tool call result:\n{obs}" if action.name != self.respond_action_name else f"User message:\n{obs}"
        return {"observation": next_green_msg, "reward": reward, "done": done, "info": {}}

    def score_submission(self) -> Dict[str, Any]:
        return score_submission_dir(self.task, submission_dir=".")
