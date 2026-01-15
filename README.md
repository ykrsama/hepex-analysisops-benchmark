# HEPEx AnalysisOps Benchmark (Green Agent)

[![Test and Publish Agent](https://github.com/ranriver/hepex-analysisops-benchmark/actions/workflows/test-and-publish.yml/badge.svg)](https://github.com/ranriver/hepex-analysisops-benchmark/actions/workflows/test-and-publish.yml)

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
docker pull ghcr.io/ranriver/hepex-analysisops-benchmark:latest

# Or build locally
docker build -t hepex-green-agent:local .

# Run (listens on port 9009)
docker run -p 9009:9009 ghcr.io/ranriver/hepex-analysisops-benchmark:latest
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
export GOOGLE_API_KEY="..."

# Run the reproduction script
uv run scripts/reproduce_locally.py --local
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
    "white_agent": "http://purple-agent:9009/"
  },
  "config": {
    "task_dirs": ["specs/zpeak_fit"],
    "data_dir": "/home/agent/output"
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
└── <release>/<dataset>/<skim>/  # Cached data files
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentBeats Platform                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ EvalRequest
┌─────────────────────────────────────────────────────────────┐
│                  Green Agent (This Repo)                     │
│  ┌──────────────┐  ┌──────────┐  ┌─────────────────────┐    │
│  │ Task Loader  │→ │ Data Mgr │→ │ Evaluation Engine   │    │
│  └──────────────┘  └──────────┘  └─────────────────────┘    │
│         │                               ▲                    │
│         ▼ A2A                           │ trace              │
│  ┌──────────────────────────────────────┴────────┐          │
│  │              Purple Agent (External)           │          │
│  └────────────────────────────────────────────────┘          │
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
