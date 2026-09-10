"""FastAPI app. Routing is a cold path."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from inbox_api.app import config
from inbox_api.app.health import health_payload
from inbox_api.app.index import index_records
from inbox_api.app.serialize import serialize_records
from inbox_api.app.store import STORE

app = FastAPI(title=config.APP_NAME, version=config.VERSION)


class RecordBatch(BaseModel):
    records: list[dict] = Field(default_factory=list)


@app.get("/health")
def health() -> dict:
    return health_payload()


@app.post("/ingest/serialize")
def ingest_serialize(batch: RecordBatch) -> dict:
    serialized = serialize_records(batch.records)
    return {"records": serialized, "count": len(serialized)}


@app.post("/ingest/index")
def ingest_index(batch: RecordBatch) -> dict:
    return index_records(batch.records)


@app.post("/reset")
def reset() -> dict:
    STORE.reset()
    return {"reset": True}
