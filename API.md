# Backtest API

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## Submit a backtest

`POST /backtest`

Returns a `job_id` immediately. The backtest runs asynchronously.

**Request body**

```json
{
  "strategy": {
    "name": "20-day breakout",
    "timescale": "day",
    "direction": "long",
    "fx_pairs": ["EUR_USD"],
    "duration": { "start": 2010, "end": 2020 },
    "rules": {
      "entry": {
        "indicator": { "source": "custom", "name": "breakout", "params": { "high": 20 } }
      },
      "exit": {
        "stop_loss": {
          "indicator": { "source": "library", "name": "atr", "params": { "period": 90 } },
          "multiplier": 1
        },
        "timeout": { "bars": 20 }
      }
    }
  }
}
```

**Fields**

| Field | Required | Notes |
|---|---|---|
| `name` | No | Label for the run |
| `timescale` | Yes | `"day"` is the only supported value |
| `direction` | Yes | `"long"` is the only supported value |
| `fx_pairs` | Yes | Array — only first pair is used currently. Available: `EUR_USD` |
| `duration` | No | Year range to load. Omit to load all available data |
| `duration.start` | No | First year to include (e.g. `2010`) |
| `duration.end` | No | Last year to include (e.g. `2020`) |
| `rules.entry.indicator.params.high` | Yes | Breakout lookback period in days |
| `rules.exit` | No | All exit conditions are optional — omit any you don't want |
| `rules.exit.stop_loss.indicator.params.period` | No | ATR period in days |
| `rules.exit.stop_loss.multiplier` | No | ATR multiplier for stop distance. Default: `1` |
| `rules.exit.timeout.bars` | No | Close trade after N bars regardless of price (stub — not yet implemented) |

**Response**

```json
{ "job_id": "f3a9a479-75e4-4715-bd8a-a5bc05460498" }
```

---

## Get results

`GET /backtest/{job_id}`

**Response**

```json
{
  "job_id": "f3a9a479-75e4-4715-bd8a-a5bc05460498",
  "status": "completed",
  "result_summary": {
    "total_trades": 42,
    "win_rate": 52.38,
    "total_return": 3241.50,
    "final_balance": 13241.50,
    "max_drawdown": 1205.00
  },
  "result_file_path": "/code/results/f3a9a479-75e4-4715-bd8a-a5bc05460498.json",
  "error": null,
  "created_at": "2026-06-18T12:55:10.266179"
}
```

**Status values:** `pending` → `running` → `completed` / `failed`

If `status` is `"failed"`, the `error` field contains the full traceback.

**Full trade detail** is written to a JSON file at `result_file_path` inside the container. To read it:

```bash
docker compose exec app cat results/{job_id}.json
```

---

## Example curl session

```bash
# Submit
JOB=$(curl -s -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{"strategy": {"name": "test", "timescale": "day", "direction": "long", "fx_pairs": ["EUR_USD"], "duration": {"start": 2015, "end": 2024}, "rules": {"entry": {"indicator": {"source": "custom", "name": "breakout", "params": {"high": 20}}}, "exit": {"stop_loss": {"indicator": {"source": "library", "name": "atr", "params": {"period": 90}}, "multiplier": 1}}}}}' \
  | python3 -m json.tool --no-ensure-ascii | grep job_id | awk -F'"' '{print $4}')

# Poll
curl http://localhost:8000/backtest/$JOB
```
