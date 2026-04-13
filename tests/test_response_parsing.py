from __future__ import annotations

from types import SimpleNamespace

from agent import Agent
from messenger import _extract_task_payload_text


def _text_part(text: str):
    return SimpleNamespace(root=SimpleNamespace(text=text))


def test_extract_task_payload_text_prefers_artifact_over_done_status():
    task = SimpleNamespace(
        artifacts=[
            SimpleNamespace(
                parts=[_text_part('{"status":"ok","artifacts":{"submission_trace.json":{"workflow_stages":[]}}}')]
            )
        ],
        status=SimpleNamespace(message=SimpleNamespace(parts=[_text_part("Done.")])),
    )
    update = SimpleNamespace(artifact=None)

    response = _extract_task_payload_text(task, update)

    assert response.startswith('{"status":"ok"')
    assert "Done." not in response


def test_extract_json_from_response_ignores_done_prefix():
    text = 'Done.{"status":"ok","artifacts":{"submission_trace.json":{"workflow_stages":[]}}}'

    extracted = Agent._extract_json_from_response(text)

    assert extracted == '{"status":"ok","artifacts":{"submission_trace.json":{"workflow_stages":[]}}}'
