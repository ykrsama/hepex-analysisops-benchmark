import json
import time
import tomllib
import dotenv
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from a2a.utils import new_agent_text_message, get_text_parts
from a2a.types import SendMessageSuccessResponse, Message

from src.green_agent.bench.env import HEPExEnv, load_task_yaml
from src.utils.tags import parse_request_tags
from src.utils.a2a_client import send_message

dotenv.load_dotenv()


def load_agent_card_toml(filename: str) -> dict:
    current_dir = __file__.rsplit("/", 1)[0]
    with open(f"{current_dir}/{filename}", "rb") as f:
        return tomllib.load(f)


async def ask_white_agent_to_solve(white_agent_url: str, env: HEPExEnv, max_num_steps: int):
    reset_res = env.reset()
    obs = reset_res["observation"]
    context_id = None

    next_green_message = env.build_task_description(obs)

    for _ in range(max_num_steps):
        resp = await send_message(white_agent_url, next_green_message, context_id=context_id)

        # Minimal parsing; structure may differ by A2A impl, adapt once you see real payload
        res_root = resp.get("result", resp)

        # If your white agent returns a2a-types JSON exactly, you'll have:
        # resp["result"]["message"]["contextId"], resp["result"]["message"]["parts"][0]["text"]
        # Adjust here based on actual response.

        # Best-effort common shape:
        msg = res_root.get("message") or res_root.get("result") or res_root
        context_id = msg.get("contextId", context_id)

        parts = msg.get("parts", [])
        text = None
        if parts and parts[0].get("type") == "text":
            text = parts[0].get("text")
        if text is None:
            # fallback
            text = json.dumps(resp)

        action = env.parse_action(text)
        step_res = env.step(action)

        if step_res["done"]:
            break

        next_green_message = step_res["observation"]

    # Deterministic scoring
    score_report = env.score_submission()
    return score_report


class HEPExGreenAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        tags = parse_request_tags(user_input)
        white_agent_url = tags["white_agent_url"]
        env_config = json.loads(tags["env_config"])

        task_spec_path = env_config["task_spec_path"]
        task = load_task_yaml(task_spec_path)

        env = HEPExEnv(
            task=task,
            runtime_limit_sec=env_config.get("runtime_limit_sec", 900),
            data_cache_dir=env_config.get("data_cache_dir", ".cache/atlas_opendata"),
        )
        max_steps = env_config.get("max_num_steps", task.get("interaction_protocol", {}).get("max_num_steps", 20))

        started = time.time()
        score_report = await ask_white_agent_to_solve(white_agent_url, env, max_steps)

        metrics = {
            "time_used_sec": time.time() - started,
            "score": score_report["score"],
            "breakdown": score_report["breakdown"],
            "paths": score_report.get("paths", {}),
        }

        ok = metrics["score"] >= 0.999
        emoji = "✅" if ok else "❌"
        await event_queue.enqueue_event(
            new_agent_text_message(
                f"Finished. White agent success: {emoji}\nMetrics:\n{json.dumps(metrics, indent=2)}\n"
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError


def start_green_agent(host="localhost", port=9001):
    agent_card_dict = load_agent_card_toml("hepex_green_agent.toml")
    agent_card_dict["url"] = f"http://{host}:{port}"

    request_handler = DefaultRequestHandler(
        agent_executor=HEPExGreenAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=AgentCard(**agent_card_dict),
        http_handler=request_handler,
    )

    uvicorn.run(app.build(), host=host, port=port)


if __name__ == "__main__":
    start_green_agent()
