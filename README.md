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

- **~2 of 3 ticks are cold** (`config.py` or `docs/**`) — gate quiet-skips, no hotspot comment. Cold PRs squash-merge.
- **~1 of 3 ticks is hot** (`serialize.py`, real AST) — detector posts last good vs this PR. About **one hotspot every 30 minutes**. Those PRs stay open as proofs (oldest closed after a few hours).

`GITHUB_TOKEN` PRs do not start other workflows, so this job runs the detector itself rather than waiting on `perf.yml`. Manual run: Actions → synthetic-traffic → Run workflow (`hot` / `cold` / `auto`).
