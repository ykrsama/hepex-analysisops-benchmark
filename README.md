# HEPEx AnalysisOps Benchmark (Green Agent)

[![Test and Publish Agent](https://github.com/hrzhao76/hepex-analysisops-benchmark/actions/workflows/test-and-publish.yml/badge.svg)](https://github.com/hrzhao76/hepex-analysisops-benchmark/actions/workflows/test-and-publish.yml)

> **AgentBeats Green Agent** for evaluating autonomous agents on high-energy physics (HEP) analysis workflows.

## Overview

This benchmark evaluates an agent's ability to perform end-to-end physics analyses using [ATLAS Open Data](https://opendata.atlas.cern/). It serves as the **Green Agent** (assessor) in the [AgentBeats](https://agentbeats.dev) ecosystem.

### Supported Tasks

| Task | Description |
|------|-------------|
| `zpeak_fit` | Extract Z mass and width from muon pairs |
| `hyy` | Measure Higgs mass using diphoton events |
| `hmumu` | Search for H→μμ using VBF topology |
| `hbb` | Identify H→bb in 0-lepton VH channel |
| `hzz` | Analyze H→ZZ→4l "Golden Channel" |
| `ttbar` | Reconstruct top quark mass |
| `wz3l` | Analyze WZ diboson in 3-lepton final state |

## Quick Start

### Docker Image

```bash
# Pull from GHCR
docker pull ghcr.io/hrzhao76/hepex-analysisops-benchmark:latest

# Or build locally
docker build -t hepex-green-agent:local .

# Run (listens on port 9009)
docker run -p 9009:9009 ghcr.io/hrzhao76/hepex-analysisops-benchmark:latest
```

### Local Development

```bash
# Install dependencies
uv sync

# Run the agent
uv run src/server.py --host 0.0.0.0 --port 9009
```

## Local Reproduction

Test the full benchmark locally with a Purple Agent:

```bash
# Set API keys
export OPENAI_API_KEY="..."
export HEPEX_OPENAI_MODEL="gpt-5"
export HEPEX_AGENT_MODEL="openai/gpt-5"

# Run the reproduction script. This default to use local ollama gpt-oss:20b.
uv run scripts/reproduce_locally.py --local

## to use 
uv run scripts/reproduce_locally.py --local --llm-provider openai --llm-model gpt-5
```

This generates a `docker-compose.yml` and runs both agents in isolated containers. Results are saved to `./output/`.

## AgentBeats Integration

### Agent Card

- **Name**: `hepex-green-agent`
- **Port**: 9009 (A2A standard)
- **Protocol**: A2A (Agent-to-Agent)

### EvalRequest Format

```json
{
  "participants": {
    "purple_agent": "http://purple-agent:9009/"
  },
  "config": {
    "task_dirs": ["tasks_public/t002_hyy_v5_l1"],
    "data_dir": "/home/agent/output",
    "input_access_mode": "local_shared_mount",
    "shared_input_dir": "/shared/hepex/input/2025e-13tev-beta/data/GamGam",
    "input_manifest_path": "/shared/hepex/input/2025e-13tev-beta/data/GamGam/input_manifest.json",
    "allow_green_download": false
  }
}
```

### Output Artifacts

Each evaluation run produces:

```
output/
├── runs/<run_id>/<task_id>/
│   ├── meta.json              # Task metadata
│   ├── submission_trace.json  # Agent response
│   ├── judge_input.json       # Evaluator input
│   └── judge_output.json      # Scored result
└── <release>/<dataset>/<skim>/  # Green-agent cache under output/

shared_input/
└── <release>/<dataset>/<skim>/  # Shared ROOT inputs for local/debug runs
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentBeats Platform                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ EvalRequest
┌─────────────────────────────────────────────────────────────┐
│                  Green Agent (This Repo)                    │
│  ┌──────────────┐  ┌──────────┐  ┌─────────────────────┐    │
│  │ Task Loader  │→ │ Data Mgr │→ │ Evaluation Engine   │    │
│  └──────────────┘  └──────────┘  └─────────────────────┘    │
│         │                               ▲                   │
│         ▼ A2A                           │ trace             │
│  ┌──────────────────────────────────────┴─────────┐         │
│  │              Purple Agent (External)           │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Reproducibility

- **Deterministic Scoring**: Rule-based checks produce identical scores for identical traces
- **Artifact Persistence**: All inputs and outputs saved as JSON for audit
- **Isolation**: Each task runs in its own directory

## Attribution

This benchmark uses **ATLAS Open Data** released under the CERN Open Data policy.

## License

See [LICENSE](LICENSE) for details.
