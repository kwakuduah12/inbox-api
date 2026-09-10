# inbox-api

A small ingest API. **This repo is the thing being watched.** Performance regression detection lives in [`hotspot-detector`](https://github.com/kwakuduah12/hotspot-detector); this service only owns the hotspot manifest, workloads, and Docker stack.

On a PR that touches `inbox_api/app/serialize.py` or `index.py`, GitHub Actions installs the detector from GitHub and runs `hotspot-detector gate`. The sticky comment is last good vs this PR. It does not block merge.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

CI installs the detector with `pip install "git+https://github.com/kwakuduah12/hotspot-detector.git@main"` and runs `hotspot-detector gate --base-ref` (no golden `--baselines` until a capture lands).

Hotspot map: `hotspot-manifest.yaml`. Cold paths (`health.py`, `config.py`) are not listed.

## Synthetic traffic (Jenkins-style)

`synthetic-traffic.yml` runs every 10 minutes on `main` (GitHub cron can drift) and opens a PR the way a periodic pipeline would cut a build:

- **Cold** (`config.py` or `docs/**`) — gate quiet-skips, then **auto-merges**.
- **Hot ok** (`serialize.py` tick marker) — detector posts last good vs this PR (`ok`). Stays open as a proof (oldest closed after a few hours).
- **Hot regression** (plants `HASH_ROUNDS = 512`) — detector posts a sticky `regression` report, then a second **autofix agent** job restores base rounds, posts a **second sticky** re-gate report (does not overwrite the first), and **auto-merges** when `ok`.

On a 10-minute cadence the pattern is roughly: cold → cold → hot → cold → cold → regression (so ~one hotspot every 30 minutes, and a planted regression about hourly).

`GITHUB_TOKEN` PRs do not start other workflows, so this job runs the detector itself rather than waiting on `perf.yml`. Manual run: Actions → synthetic-traffic → Run workflow (`auto` / `cold` / `hot` / `regression`).
