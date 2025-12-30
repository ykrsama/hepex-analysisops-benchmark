"""
Launcher module - initiates and coordinates the evaluation process (HEPEx).
"""

import multiprocessing
import json
import asyncio

from src.green_agent.agent import start_green_agent
from src.white_agent.agent import start_white_agent

from src.utils.a2a_client import send_message, wait_agent_ready


async def launch_evaluation():
    # ---- start green agent ----
    print("Launching green agent...")
    green_address = ("localhost", 9527)
    green_url = f"http://{green_address[0]}:{green_address[1]}"
    p_green = multiprocessing.Process(
        target=start_green_agent,
        args=("hepex_green_agent", *green_address),  # (agent_name, host, port)
    )
    p_green.start()
    assert await wait_agent_ready(green_url), "Green agent not ready in time"
    print("Green agent is ready.")

    # ---- start white agent ----
    print("Launching white agent...")
    white_address = ("localhost", 9022)
    white_url = f"http://{white_address[0]}:{white_address[1]}"
    p_white = multiprocessing.Process(
        target=start_white_agent,
        args=("hepex_white_baseline", *white_address),  # (agent_name, host, port)
    )
    p_white.start()
    assert await wait_agent_ready(white_url), "White agent not ready in time"
    print("White agent is ready.")

    # ---- send task to green agent ----
    print("Sending task description to green agent...")

    # Minimal env config for your HEPEx green agent
    task_config = {
        "task_spec_path": "src/green_agent/bench/tasks/zll/task1_run/task.yaml",
        "runtime_limit_sec": 900,
        "max_num_steps": 20,
        "data_cache_dir": ".cache/atlas_opendata",
        "data_policy": "fetch_by_benchmark",
        "seed": 123,
    }

    task_text = f"""
Your task is to instantiate HEPEx benchmark to test the agent located at:
<white_agent_url>
{white_url}/
</white_agent_url>

You should use the following env configuration:
<env_config>
{json.dumps(task_config, indent=2)}
</env_config>
""".strip()

    print("Task description:")
    print(task_text)
    print("Sending...")
    response = await send_message(green_url, task_text)
    print("Response from green agent:")
    print(json.dumps(response, indent=2))

    print("Evaluation complete. Terminating agents...")
    p_green.terminate()
    p_green.join()
    p_white.terminate()
    p_white.join()
    print("Agents terminated.")


def main():
    asyncio.run(launch_evaluation())


if __name__ == "__main__":
    main()
