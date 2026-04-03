from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from tech_new_writer.env_loader import load_local_env
from tech_new_writer.service import (
    DEFAULT_SOURCES,
    DEFAULT_TOPIC,
    FlowResult,
    run_daily_top_flow,
    run_single_article_flow,
    run_topic_flow,
)


load_local_env()

app = FastAPI(title="tech_new_writer API", version="0.1.0")


class TopicRunRequest(BaseModel):
    topic: str = Field(default=DEFAULT_TOPIC, min_length=1)
    sources: str = Field(default=DEFAULT_SOURCES, min_length=1)
    publish_draft: bool | None = None


class SingleArticleRunRequest(BaseModel):
    source_url: str = Field(min_length=1)
    publish_draft: bool | None = None


class DailyTopRunRequest(BaseModel):
    sources: str = Field(default=DEFAULT_SOURCES, min_length=1)
    publish_draft: bool | None = None


class FlowResultResponse(BaseModel):
    status: str
    flow: str
    topic: str | None
    sources: list[str]
    result: Any
    draft_article_path: str | None
    final_article_path: str | None
    final_article_markdown: str | None
    publish_result: dict[str, str] | None
    top_article_url: str | None
    original_title: str | None

    @classmethod
    def from_flow_result(cls, value: FlowResult) -> "FlowResultResponse":
        return cls(**value.__dict__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs/topic", response_model=FlowResultResponse)
def run_topic(request: TopicRunRequest) -> FlowResultResponse:
    try:
        result = run_topic_flow(
            topic=request.topic,
            sources=request.sources,
            publish_draft=request.publish_draft,
        )
        return FlowResultResponse.from_flow_result(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/runs/single-article", response_model=FlowResultResponse)
def run_single_article(request: SingleArticleRunRequest) -> FlowResultResponse:
    try:
        result = run_single_article_flow(
            source_url=request.source_url,
            publish_draft=request.publish_draft,
        )
        return FlowResultResponse.from_flow_result(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/runs/daily-top", response_model=list[FlowResultResponse])
def run_daily_top(request: DailyTopRunRequest) -> list[FlowResultResponse]:
    try:
        results = run_daily_top_flow(
            sources=request.sources,
            publish_draft=request.publish_draft,
        )
        return [FlowResultResponse.from_flow_result(item) for item in results]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
