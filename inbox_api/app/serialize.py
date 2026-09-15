"""Hot path: CPU-bound record serialization.

This file is a hotspot: PRs that touch it should trigger ingest_bulk.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

HASH_ROUNDS = 512
_SYNTHETIC_TICK = "20260915T225642Z"


def _effective_rounds() -> int:
    extra = int(os.environ.get("HOTSPOT_SLOWDOWN_ROUNDS", "0") or 0)
    return HASH_ROUNDS + extra


def serialize_records(records: list[dict]) -> list[dict]:
    extra_ms = float(os.environ.get("HOTSPOT_SLOWDOWN_MS", "0") or 0)
    if extra_ms > 0:
        time.sleep(extra_ms / 1000.0)

    rounds = _effective_rounds()
    out: list[dict] = []
    for record in records:
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        for i in range(rounds):
            digest = hashlib.sha256(f"{digest}:{i}".encode("utf-8")).hexdigest()
        out.append(
            {
                **record,
                "_digest": digest,
                "_size": len(payload),
                "_normalized": payload,
                "_synthetic_tick": _SYNTHETIC_TICK,
            }
        )
    return out
