"""
CLI entry point for HEPEx (Agentified HEP AnalysisOps Benchmark).
"""

import typer
import asyncio
import sys
from pathlib import Path

from src.green_agent.agent import start_green_agent
from src.white_agent.agent import start_white_agent
from src.launcher import launch_evaluation

app = typer.Typer(
    help="HEPEx - Agentified HEP AnalysisOps Benchmark (AgentBeats-compatible)"
)


@app.command()
def green(
    host: str = typer.Option("localhost", help="Host to bind the green agent"),
    port: int = typer.Option(9527, help="Port for the green agent"),
):
    """Start the green agent (assessment manager)."""
    start_green_agent(host=host, port=port)


@app.command()
def white(
    host: str = typer.Option("localhost", help="Host to bind the white agent"),
    port: int = typer.Option(9022, help="Port for the white agent"),
):
    """Start the white agent (baseline target agent)."""
    start_white_agent(host=host, port=port)


@app.command()
def launch():
    """Launch the complete evaluation workflow."""
    asyncio.run(launch_evaluation())


if __name__ == "__main__":
    app()
