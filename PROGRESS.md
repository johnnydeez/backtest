# Backtest Project — Progress Log

**Date:** 2026-03-30

---

## What We Built Today

We implemented the first end-to-end MVP of the forex backtesting application. The goal was to use the full stack (FastAPI, Celery, Redis, PostgreSQL, pandas) in the simplest possible form so we could learn how all the pieces fit together.

### Stack
- **Language:** Python 3.12
- **API:** FastAPI + Uvicorn
- **Job Queue:** Celery + Redis
- **Database:** PostgreSQL (via SQLAlchemy)
- **Data / Indicators:** pandas, pandas-ta (ATR), custom (N-day high)
- **Infrastructure:** Docker + docker-compose

---

## Project Structure

```
backtest/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── data/
│   └── 2005_EUR_USD.csv          # Only data file for MVP
├── results/                       # JSON detail files written here per job
└── app/
    ├── main.py                    # FastAPI entry point, creates DB tables on startup
    ├── worker.py                  # Celery app config
    ├── api/
    │   └── routes.py              # POST /backtest, GET /backtest/{job_id}
    ├── db/
    │   ├── database.py            # SQLAlchemy engine + session + Base
    │   └── models.py              # BacktestJob table
    ├── engine/
    │   ├── params.py              # BacktestParams: loads CSV, pre-calculates indicators
    │   ├── loop.py                # BacktestLoop: bar-by-bar iteration
    │   ├── state.py               # TestState: tracks balance, position, trades
    │   ├── indicators/
    │   │   ├── custom.py          # n_day_high (breakout indicator)
    │   │   └── library.py        # atr (wraps pandas-ta)
    │   └── rules/
    │       ├── entry.py           # BreakoutEntryRule
    │       └── exit.py            # ATRStopLossRule
    └── tasks/
        └── backtest_task.py       # Celery task: runs engine, writes results to DB + disk
```

---

## Key Design Decisions Made

### Strategy JSON Format
All trading logic lives under a `rules` key. Top-level keys are metadata only.
```json
{
  "name": "20-Day High Breakout with ATR Stop",
  "timescale": "day",
  "direction": "long",
  "fx_pairs": ["EUR_USD"],
  "rules": {
    "entry": {
      "indicator": { "source": "custom", "name": "breakout", "params": {"high": 20} }
    },
    "stop_loss": {
      "indicator": { "source": "library", "name": "atr", "params": {"period": 90} },
      "multiplier": 1
    }
  }
}
```

### Rules Architecture
- **Indicators** (`engine/indicators/`) — pure calculations on price data, pre-calculated upfront
- **Rules** (`engine/rules/`) — if/then logic evaluated bar-by-bar
- Exit rules return a reason string if triggered, `None` if not — the loop is agnostic about why a trade closes
- A **rule registry** (TODO) will eventually map JSON `"name"` values to classes so the loop never needs to change as new rules are added

### P&L Calculation
- P&L is calculated in pips first, then converted to dollars
- JPY pairs use pip multiplier `0.01`, all others `0.0001`
- MVP uses fixed 100,000 units (1 standard lot)
- `pip_dollar_value` TODO: currently only correct for USD-quoted pairs (EUR_USD etc.)

### Balance vs Equity
- `balance` = realized P&L only
- `equity` = balance + unrealized (open position)
- Drawdown tracked against equity peak, not balance peak

### Results Storage
- **Summary metrics** (total trades, win rate, total return, max drawdown) → saved to PostgreSQL
- **Full detail** (every trade entry/exit) → saved as JSON file on disk, DB stores the file path
- Failed jobs store the full Python traceback in the `error` DB column

### Data Files
- Format: `{year}_{pair}.csv` (e.g. `2005_EUR_USD.csv`)
- Columns: `timestamp, open, high, low, close`
- Timestamps include timezone: `2005-01-03 22:00:00+00:00`
- Currently only `2005_EUR_USD.csv` is in the project

---

## Known TODOs (in code)

1. **Rule registry** — map JSON names to rule classes so rules are built dynamically from JSON
2. **`_pip_dollar_value`** — only correct for USD-quoted pairs; needs to handle JPY, inverse, and cross pairs
3. **Entry/exit timing** — currently enters/exits at current bar's close; should use next bar's open (look-ahead bias)
4. **Strategy request body** — currently wrapped in `{"strategy": {...}}`; should accept strategy directly per strict REST design
5. **Database migrations (Alembic)** — currently using `create_all()` on startup; schema changes require wiping the postgres volume

---

## Where We Are Now

All code is written. We ran `docker compose up` for the first time and hit two issues:

### Issue 1 — Fixed: Race condition (app starts before postgres is ready)
- **Problem:** `depends_on` only waits for the container to start, not for postgres to be accepting connections
- **Fix:** Added a `healthcheck` to the postgres service using `pg_isready`, and changed `depends_on` to use `condition: service_healthy`

### Issue 2 — Fixed: Celery task not discovered
- **Problem:** `autodiscover_tasks(["app.tasks"])` looks for `app/tasks/tasks.py` but our file is `backtest_task.py`
- **Fix:** Changed to `celery_app.conf.include = ["app.tasks.backtest_task"]` in `worker.py`

**We have not yet restarted the containers with these fixes applied.** That is the immediate next step.

---

## What To Do Next (In Order)

1. **`docker compose down` then `docker compose up`** — verify the fixes work:
   - App should start cleanly (no postgres connection error)
   - Worker should show `app.tasks.backtest_task.run_backtest` in `[tasks]`

2. **Submit a test job** — using curl or the FastAPI auto-docs at `http://localhost:8000/docs`:
   ```bash
   curl -X POST http://localhost:8000/backtest \
     -H "Content-Type: application/json" \
     -d '{"strategy": {"name": "test", "timescale": "day", "direction": "long", "fx_pairs": ["EUR_USD"], "rules": {"entry": {"indicator": {"source": "custom", "name": "breakout", "params": {"high": 20}}}, "stop_loss": {"indicator": {"source": "library", "name": "atr", "params": {"period": 90}}, "multiplier": 1}}}}'
   ```

3. **Poll for results:**
   ```bash
   curl http://localhost:8000/backtest/{job_id}
   ```

4. **If anything fails** — check `job.error` in the response for the full traceback, and check worker logs

5. **Once end-to-end works**, decide what to improve first:
   - More data files (multiple years)
   - Additional rule types (take profit)
   - Fix the entry/exit timing look-ahead bias
   - Position sizing improvements
   - Additional currency pairs
