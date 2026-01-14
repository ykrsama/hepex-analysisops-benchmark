import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

# A2A official client bits (module paths may differ slightly by version)
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

@pytest.mark.asyncio
async def test_green_agent_a2a_send_message(tmp_path_factory):
    env = os.environ.copy()
    tmpdir = tmp_path_factory.mktemp("green_server")
    data_dir = tmpdir / "atlas_cache"
    data_dir.mkdir(parents=True, exist_ok=True)
    env["HEPEX_DATA_DIR"] = str(data_dir)

    green_server = {
        "base_url": "http://localhost:9001",
        "data_dir": Path(env["HEPEX_DATA_DIR"]),
    }
    base_url = green_server["base_url"]
    data_dir: Path = green_server["data_dir"]

    # Build EvalRequest JSON payload (this is what your Agent.run parses via EvalRequest.model_validate_json)
    eval_request = {
        "participants": {},  # mock mode: no white agent
        "config": {
            "data_dir": str(data_dir),
            "tasks": [
                {
                    "id": "t001_zpeak_fit",
                    "type": "zpeak_fit",
                    "mode": "mock",
                    "needs_data": True,  # avoid network in integration test
                    "release": "2025e-13tev-beta",
                    "dataset": "data",
                    "skim": "2muons",
                    "protocol": "https",
                    "max_files": 1,
                    "cache": True,
                    "reuse_existing": True,
                    "workflow_spec_path": "specs/zpeak_fit/workflow.yaml",
                    "rubric_path": "specs/zpeak_fit/rubric.yaml",
                    "judge_prompt_path": "specs/zpeak_fit/judge_prompt.md",
                }
            ],
        },
    }

    # Send as A2A "message" with a single text part containing JSON
    send_message_payload = {
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": json.dumps(eval_request)}],
            "messageId": uuid4().hex,
        }
    }

    async with httpx.AsyncClient(timeout=300.0) as httpx_client:
        # 1) Resolve agent card (this discovers correct endpoints; avoids 404 guessing)
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        final_agent_card = await resolver.get_agent_card()

        # 2) Create A2A client
        client = A2AClient(httpx_client=httpx_client, agent_card=final_agent_card)

        # 3) Send message
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
        response = await client.send_message(request)

    # Basic response sanity
    resp_json = response.model_dump(mode="json", exclude_none=True)
    assert resp_json is not None

    # Hard proof: run artifacts should exist
    runs_root = data_dir / "runs"
    assert runs_root.exists(), f"runs/ not created at {runs_root}"

    run_dirs = [p for p in runs_root.iterdir() if p.is_dir()]
    assert len(run_dirs) >= 1, f"No run dirs found in {runs_root}"

    # Pick latest run dir (by name sort works with your timestamp prefix)
    run_dir = sorted(run_dirs)[-1]
    task_dir = run_dir / "t001_zpeak_fit"
    assert task_dir.exists(), f"Task dir missing: {task_dir}"

    for fname in ["meta.json", "submission_trace.json", "judge_input.json", "judge_output.json"]:
        assert (task_dir / fname).exists(), f"Missing {fname} under {task_dir}"
