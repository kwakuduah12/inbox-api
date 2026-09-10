#!/usr/bin/env python3
"""Apply a synthetic agent change for the scheduled traffic job.

Hot ticks touch serialize.py (real AST) so the detector comments.
Cold ticks touch config.py or docs/ so the gate quiet-skips.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SERIALIZE = REPO / "inbox_api" / "app" / "serialize.py"
CONFIG = REPO / "inbox_api" / "app" / "config.py"
TRAFFIC_LOG = REPO / "docs" / "traffic-log.md"
TICK_RE = re.compile(r'^_SYNTHETIC_TICK = "[^"]*"$', re.M)
VERSION_RE = re.compile(r'^VERSION = "[^"]*"$', re.M)

RECORD_BLOCK = """            {
                **record,
                "_digest": digest,
                "_size": len(payload),
                "_normalized": payload,
            }"""

RECORD_BLOCK_TICK = """            {
                **record,
                "_digest": digest,
                "_size": len(payload),
                "_normalized": payload,
                "_synthetic_tick": _SYNTHETIC_TICK,
            }"""


def decide_kind(forced: str) -> tuple[str, str]:
    """Return (kind, cold_target). kind is hot or cold."""
    if forced == "hot":
        return "hot", ""
    if forced == "cold":
        slot = int(time.time()) // 600
        return "cold", "docs" if slot % 2 else "config"
    slot = int(time.time()) // 600
    if slot % 3 == 0:
        return "hot", ""
    return "cold", "docs" if slot % 3 == 1 else "config"


def apply_hot(tick: str) -> list[str]:
    text = SERIALIZE.read_text()
    assignment = f'_SYNTHETIC_TICK = "{tick}"'
    if TICK_RE.search(text):
        text = TICK_RE.sub(assignment, text)
    else:
        if "HASH_ROUNDS = 256\n" not in text:
            raise SystemExit("serialize.py: HASH_ROUNDS not found")
        text = text.replace("HASH_ROUNDS = 256\n", f"HASH_ROUNDS = 256\n{assignment}\n", 1)
        if RECORD_BLOCK not in text:
            raise SystemExit("serialize.py: record block not found")
        text = text.replace(RECORD_BLOCK, RECORD_BLOCK_TICK, 1)
    SERIALIZE.write_text(text)
    return ["inbox_api/app/serialize.py"]


def apply_cold_config(tick: str) -> list[str]:
    text = CONFIG.read_text()
    if not VERSION_RE.search(text):
        raise SystemExit("config.py: VERSION not found")
    CONFIG.write_text(VERSION_RE.sub(f'VERSION = "0.1.0+{tick}"', text, count=1))
    return ["inbox_api/app/config.py"]


def apply_cold_docs(tick: str) -> list[str]:
    TRAFFIC_LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"- `{stamp}` synthetic cold tick `{tick}` (docs-only; detector should skip)\n"
    if TRAFFIC_LOG.exists():
        TRAFFIC_LOG.write_text(TRAFFIC_LOG.read_text() + line)
    else:
        TRAFFIC_LOG.write_text(
            "# Synthetic traffic log\n\n"
            "Cold-path ticks from the scheduled Jenkins-style job. Listed in "
            "`exclude_paths`, so they must not trigger ingest_bulk.\n\n" + line
        )
    return ["docs/traffic-log.md"]


def write_github_output(values: dict[str, str]) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        for key, value in values.items():
            print(f"{key}={value}")
        return
    with Path(path).open("a", encoding="utf-8") as fh:
        for key, value in values.items():
            fh.write(f"{key}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["auto", "hot", "cold"], default="auto")
    args = parser.parse_args()
    tick = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    kind, cold_target = decide_kind(args.kind)
    if kind == "hot":
        files = apply_hot(tick)
        title = f"Synthetic hotspot: serialize tick {tick}"
        body = (
            "Scheduled synthetic **hotspot** PR (Jenkins-style traffic).\n\n"
            "Touches `serialize.py` with a real AST change so hotspot-detector "
            "should post last good vs this PR. Not a planted slowdown."
        )
        label = "hotspot"
    elif cold_target == "docs":
        files = apply_cold_docs(tick)
        title = f"Synthetic cold: docs tick {tick}"
        body = (
            "Scheduled synthetic **cold** PR. Docs-only; detector should quiet-skip."
        )
        label = "cold"
    else:
        files = apply_cold_config(tick)
        title = f"Synthetic cold: config tick {tick}"
        body = (
            "Scheduled synthetic **cold** PR. `config.py` is not a hotspot; "
            "detector should quiet-skip."
        )
        label = "cold"
    write_github_output(
        {
            "kind": kind,
            "label": label,
            "title": title,
            "tick": tick,
            "files": " ".join(files),
        }
    )
    Path("/tmp/synthetic-pr-body.md").write_text(body + "\n")
    print(f"kind={kind} label={label} files={files}", file=sys.stderr)


if __name__ == "__main__":
    main()
