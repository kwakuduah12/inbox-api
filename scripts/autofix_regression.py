#!/usr/bin/env python3
"""Autofix agent: undo a planted serialize slowdown after a regression signal.

Restores HASH_ROUNDS to the base value while keeping the synthetic tick marker
so the PR still has a real AST change, then the workflow re-gates and merges.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SERIALIZE = REPO / "inbox_api" / "app" / "serialize.py"
HASH_ROUNDS_RE = re.compile(r"^HASH_ROUNDS = \d+$", re.M)
BASE_HASH_ROUNDS = 256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--compare",
        type=Path,
        default=Path("results/compare.json"),
        help="Gate compare JSON; must report overall=regression to proceed.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Apply the fix even if compare is missing or not regression.",
    )
    args = parser.parse_args()

    if not args.force:
        if not args.compare.is_file():
            print(f"no compare file at {args.compare}; nothing to fix", file=sys.stderr)
            raise SystemExit(0)
        payload = json.loads(args.compare.read_text())
        overall = payload.get("overall")
        if overall != "regression":
            print(f"overall={overall!r}; autofix only runs on regression", file=sys.stderr)
            raise SystemExit(0)

    text = SERIALIZE.read_text()
    if not HASH_ROUNDS_RE.search(text):
        raise SystemExit("serialize.py: HASH_ROUNDS not found")
    match = HASH_ROUNDS_RE.search(text)
    assert match is not None
    before = match.group(0)
    text = HASH_ROUNDS_RE.sub(f"HASH_ROUNDS = {BASE_HASH_ROUNDS}", text, count=1)
    SERIALIZE.write_text(text)
    print(f"autofix: {before} -> HASH_ROUNDS = {BASE_HASH_ROUNDS}")
    if before == f"HASH_ROUNDS = {BASE_HASH_ROUNDS}":
        print(
            "warning: rounds already at base; planted slowdown may use another lever",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
