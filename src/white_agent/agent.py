import json
import re
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from a2a.utils import new_agent_text_message

# ---- helpers ----
def extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    return m.group(1).strip() if m else ""

def has_tool(tools_info_text: str, tool_name: str) -> bool:
    return f'"name": "{tool_name}"' in tools_info_text or f"'name': '{tool_name}'" in tools_info_text

def make_action(name: str, kwargs: dict) -> str:
    return f"<json>{json.dumps({'name': name, 'kwargs': kwargs})}</json>"

class BaselineWhiteAgentExecutor(AgentExecutor):
    """
    A dumb baseline:
      step0: run analysis
      step1: check outputs
      step2: respond done
    Uses context_id to keep a tiny state machine.
    """
    def __init__(self):
        self._state_by_context = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = context.get_user_input()
        ctx_id = context.context_id  # a2a context id

        # initialize state
        st = self._state_by_context.get(ctx_id, {"step": 0})
        step = st["step"]

        # crude detection: green's first message contains tools_info dump
        # (we won't fully parse it; just assume 'run' exists)
        if step == 0:
            st["step"] = 1
            self._state_by_context[ctx_id] = st
            msg = make_action("run", {"cmd": "python analysis/run_analysis.py", "cwd": ".", "timeout_sec": 300})
            await event_queue.enqueue_event(new_agent_text_message(msg))
            return

        if step == 1:
            # after running, check expected outputs
            st["step"] = 2
            self._state_by_context[ctx_id] = st
            msg = make_action("file_exists", {"path": "fit_results.json"})
            await event_queue.enqueue_event(new_agent_text_message(msg))
            return

        # final step: respond (end)
        msg = make_action("respond", {"content": "Done. I ran the analysis and verified outputs."})
        await event_queue.enqueue_event(new_agent_text_message(msg))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

def start_white_agent(host="localhost", port=9002):
    # minimal card (you can load from toml if you want)
    agent_card = AgentCard(
        name="hepex_white_baseline",
        description="Minimal baseline agent for HEPEx",
        version="0.1.0",
        url=f"http://{host}:{port}",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities={"streaming": False},
        skills=[{
            "id": "solve",
            "name": "Solve",
            "description": "Run analysis and verify outputs.",
            "tags": ["baseline"]
        }]
    )

    handler = DefaultRequestHandler(
        agent_executor=BaselineWhiteAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler)
    uvicorn.run(app.build(), host=host, port=port)

if __name__ == "__main__":
    start_white_agent()
