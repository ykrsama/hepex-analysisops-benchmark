from __future__ import annotations
from typing import Literal, Union
from pydantic import BaseModel, Field

class ZPeakFitTaskSpec(BaseModel):
    # --- task identity ---
    id: str = "t001_zpeak_fit"
    type: Literal["zpeak_fit"] = "zpeak_fit"
    mode: Literal["mock", "call_white"] = "mock"

    # --- data requirements ---
    needs_data: bool = True
    release: str = "2025e-13tev-beta"
    dataset: str = "data"
    skim: str = "2muons"
    protocol: str = "https"
    max_files: int = 3
    cache: bool = True # reserved for future use
    reuse_existing: bool = True  

    # --- workflow & evaluation ---
    workflow_spec_path: str = "specs/zpeak_fit/workflow.yaml"
    rubric_path: str = "specs/zpeak_fit/rubric.yaml"
    judge_prompt_path: str = "specs/zpeak_fit/judge_prompt.md"

class HyyAnalysisTaskSpec(BaseModel):
    # --- task identity ---
    id: str = "t002_hyy"
    type: Literal["hyy_analysis"] = "hyy_analysis"
    mode: Literal["mock", "call_white"] = "mock"

    # --- data requirements ---
    needs_data: bool = True
    release: str = "2025e-13tev-beta"
    dataset: str = "data"
    skim: str = "2photons"
    protocol: str = "https"
    max_files: int = 3
    cache: bool = True
    reuse_existing: bool = True

    # --- workflow & evaluation ---
    workflow_spec_path: str = "specs/hyy/workflow.yaml"
    rubric_path: str = "specs/hyy/rubric.yaml"
    judge_prompt_path: str = "specs/hyy/judge_prompt.md"

TaskSpec = Union[ZPeakFitTaskSpec, HyyAnalysisTaskSpec]

class GreenConfig(BaseModel):
    data_dir: str = "/tmp/atlas_data_cache"
    tasks: list[TaskSpec] = Field(default_factory=lambda: [ZPeakFitTaskSpec(), HyyAnalysisTaskSpec()])
