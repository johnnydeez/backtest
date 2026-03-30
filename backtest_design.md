# Forex Backtesting Application - Design Document

## Overall Goal

Build a currency backtesting trading application for **forex pairs only** (starting with daily timeframes). The system is designed to be **strategy-agnostic** - allowing users to define and test different trading strategies without modifying the core backtesting engine.

**Future Vision:** Eventually connect a UI where users can visually design strategies. The UI would generate JSON configurations that get sent to the Python backend for backtesting.

**Current Focus:** Build the smallest possible working MVP while keeping the full architecture in mind.

---

## Strategy Definition (JSON Format)

Strategies are defined as JSON objects that can be passed to the backtesting engine. The structure is **declarative** - the presence of specific keys determines the type of logic being used.

### Example Strategy: 20-Day High Breakout with ATR Stop

```json
{
  "name": "20-Day High Breakout with ATR Stop",
  "timescale": "day",
  "direction": "long",
  "fx_pairs": ["EUR_USD"],
  "rules": {
    "entry": {
      "indicator": {
        "source": "custom",
        "name": "breakout",
        "params": {"high": 20}
      }
    },
    "stop_loss": {
      "indicator": {
        "source": "library",
        "name": "atr",
        "params": {"period": 90}
      },
      "multiplier": 1
    },
    "take_profit": {
      "trailing": {
        "pips": 20
      }
    }
  }
}
```

### Key Design Decisions

1. **Top-level vs rules separation** - Top-level keys are strategy metadata (`name`, `timescale`, `direction`, `fx_pairs`). All if/then trading logic lives under `rules`. This keeps the structure clean as the number of rule types grows (e.g. time filters, margin limits, position sizing rules can all be added under `rules` without cluttering the top level).

2. **No redundant "type" fields** - Structure determines type (if `indicator` key exists, it's indicator-based; if `price` key exists, it's price-based, etc.)

3. **Indicator source distinction**:
   - `"source": "custom"` - Custom logic we write (e.g., breakout detection)
   - `"source": "library"` - Standard technical indicators from libraries like TA-Lib or pandas-ta (e.g., ATR, RSI, MACD)

4. **Clear parameter ownership** - Nested objects show that parameters belong to the indicator, not the entry/exit rule
   ```json
   "indicator": {
     "name": "breakout",
     "params": {"high": 20}  // These params belong to breakout, not to entry
   }
   ```

5. **Consistent pattern across all rules** - All rules under `rules` follow the same structural approach

---

## Architecture Overview

### High-Level Flow Diagram

```
┌─────────────────┐
│    UI / JSON    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐        ┌──────────────────┐
│       API       │◀──────▶│    DATABASE (PG) │
└────────┬────────┘        └──────────────────┘
         │                          ▲
         ▼                          │
┌─────────────────┐        ┌────────┴─────────┐
│   JOB QUEUE     │        │     RESULT       │
│ (Celery/Redis)  │        │  summary metrics │
└────────┬────────┘        └────────┬─────────┘
         │                          │
         ▼                 ┌────────┴─────────┐
┌──────────────────────────────────────────────┐
│              BACKTEST ENGINE                 │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │           BACKTEST PARAMS              │  │
│  │   [Indicator Logic] [History Data CSV] │  │
│  └─────────────────┬──────────────────────┘  │
│                    │                          │
│                    ▼                          │
│  ┌─────────────────────────┐                 │
│  │      BACKTEST LOOP      │◀──▶ TEST STATE  │
│  └─────────────────────────┘                 │
└──────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  STATE DETAILS FILE │
│      (JSON)         │
└─────────────────────┘
```

### How It Works

1. UI (or CLI for MVP) submits a strategy JSON to the **API**
2. API validates the request, then hands it to the **Job Queue**
3. Job Queue assigns it to a **Celery worker** which runs the backtest engine asynchronously
4. API immediately returns a job ID to the caller — it does not wait for the backtest to finish
5. Inside the engine, **BacktestParams** loads CSV data and pre-calculates all indicators
6. **BacktestLoop** iterates bar-by-bar, delegating decisions to rule objects, and reads/writes **TestState**
7. When complete, **Result** is produced:
   - Summary metrics are sent to the **API**, which saves them to the **database**
   - Detailed state data (equity curve, trade log, drawdown, etc.) is written to a **JSON file on disk**
   - The database record stores a pointer to the JSON file
8. The caller can poll the API for job status and retrieve results when ready

### Concurrency

Each test run gets its own isolated instance of the engine — its own `BacktestParams`, `BacktestLoop`, and `TestState` in memory. Celery workers handle this naturally; no shared state exists between runs.

---

## Component Responsibilities

### 1. API (FastAPI)

**Purpose:** Single external interface for all system interactions

**Responsibilities:**
- Receive strategy JSON from UI or CLI
- Authentication and request validation
- Route requests (submit backtest, fetch results, manage strategies, user accounts)
- Submit jobs to the job queue and return job IDs
- Direct read/write to the database for non-backtest operations
- Receive completed results and persist them (DB summary + JSON file)

### 2. Job Queue (Celery + Redis)

**Purpose:** Async job management

**Responsibilities:**
- Accept backtest jobs from the API
- Distribute jobs to available workers
- Allow the API to remain responsive during long-running tests

### 3. Backtest Engine

Self-contained — knows nothing about the API, database, or job queue. Takes JSON in, returns a result.

#### 3a. BacktestParams (Python Class)

**Purpose:** Pre-calculation and data preparation phase

**Responsibilities:**
- Parse and validate strategy JSON
- Load historical price data from CSV files (using pandas)
- Pre-calculate ALL indicators for the entire date range
- Package everything the loop needs

**Key Concept - Indicators vs. Signals:**
- **Indicators** = Pure, stateless functions that analyze price data
  - Examples: ATR values, 20-day high, RSI, MACD
  - Can ALL be pre-calculated upfront
  - Output: Arrays of calculated values for each bar

- **Signals/Rules** = Strategy logic that uses indicators + trade state
  - Examples: Entry conditions, stop loss placement, trailing take profit
  - Cannot be pre-calculated (depend on position state)
  - Handled in BacktestLoop

**Why Pre-calculate?**
- **Performance:** Calculate ATR once for 5000 days using vectorized operations vs. recalculating 5000 times
- **Simplicity:** Loop just checks conditions against pre-existing values
- **Debuggability:** Can inspect all indicator values before running the backtest

#### 3b. BacktestLoop (Python Class)

**Purpose:** Orchestrate bar-by-bar execution

**Responsibilities:**
- Iterate through historical data bar-by-bar
- Delegate entry/exit decisions to rule objects (e.g., EntryRule, StopLoss, TakeProfit)
- Read from and write to TestState each bar
- Does NOT contain decision logic itself — only orchestrates

**Note:** Does NOT calculate indicators — only uses pre-calculated values from BacktestParams

#### 3c. TestState (Python Class)

**Purpose:** Track all position and account state during execution

**Responsibilities:**
- Current position (in trade or not)
- Entry price, entry date
- Stop loss level, take profit level
- Account balance, P&L, drawdown
- Trade history

#### 3d. Rule Objects

**Purpose:** Encapsulate entry/exit decision logic

**Examples:** EntryRule, StopLossRule, TakeProfitRule

The loop calls these objects — they return decisions based on current bar data and state. Strategy logic lives here, not in the loop.

### 4. Result

**Purpose:** Output of the backtest, split into two formats:

- **Summary** (to database via API): High-level metrics — total return, max drawdown, number of trades, Sharpe ratio, etc. Used for listing and comparing results.
- **Detail file** (JSON on disk): Full equity curve, every trade entry/exit, bar-by-bar drawdown — everything needed to render charts. The database record stores the file path.

---

## Data Format

**Historical Data:**
- Daily forex data stored as CSV files
- Format: One file per currency pair per year (e.g., `EUR_USD_2020.csv`, `EUR_USD_2021.csv`)
- Each row represents one trading day with: date, open, high, low, close
- Exact format details to be determined during implementation

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| API | FastAPI |
| Job Queue | Celery |
| Message Broker | Redis |
| Database | PostgreSQL |
| Data / Indicators | pandas, pandas-ta or ta-lib, numpy |
| Result Detail Storage | JSON files on disk |

---

## Design Principles

1. **Strategy-agnostic architecture** - Core engine doesn't know about specific strategies
2. **Declarative configuration** - Strategies defined as data (JSON), not code
3. **Separation of concerns** - Data prep, execution, state management, and API are distinct layers
4. **API as single interface** - All external interactions go through the API; the engine is pure computation
5. **Async by default** - Jobs are queued; the API never blocks waiting for a backtest to finish
6. **Isolated runs** - Each backtest gets its own in-memory engine instance; no shared state between runs
7. **Clarity over brevity** - Nested structures show parameter ownership explicitly
8. **Vectorized approach** - Pre-calculate what can be pre-calculated for performance
9. **Avoid look-ahead bias** - When pre-calculating, only use data available at each point in time

---

## Open Questions

- Position sizing rules
- How to handle commission/spread/slippage
- Error handling and validation strategies
- Testing strategy for the backtester itself
- Event-driven vs. vectorized loop implementation (leaning vectorized for MVP)

---

## Engine Implementation Notes (From Existing Backtester)

These are lessons carried forward from the existing `fx-robots/backtester` scripts.

### Pip Calculations
P&L must be calculated in pips first, then converted to dollars — not as raw price difference.
- Non-JPY pairs: pip multiplier = `0.0001`
- JPY pairs: pip multiplier = `0.01`
- Formula: `pip_profit = (exit_price - entry_price) / pip_multiplier` (for long)
- Dollar profit: `pip_profit × pip_dollar_value`

### Position Sizing
Dollar P&L is meaningless without position size. MVP uses fixed units (e.g. 100,000 = 1 standard lot).
- `pip_dollar_value = (units / 100,000) × 10` for USD-quoted pairs (e.g. EUR_USD)
- Position sizing by pip value or compounding are deferred to later versions.

### Balance vs Equity
- `balance` = realized P&L only (closed trades)
- `equity` = balance + unrealized P&L (open trades)
- Drawdown must be tracked against **equity peak**, not balance peak

### Trade State Structure
Each trade should track: pair, direction, entry price, entry date, exit price, exit date, pip profit, dollar profit, exit reason. Separating `active_trades` from `closed_trades` (with a unified `trade_history` audit list) is cleaner than a single list.

### What We're Leaving Out for MVP
Partial closures, margin tracking, finance/swap fees, compounding, multiple simultaneous positions.

---

## Known Future Work (Deferred Intentionally)

### Database Migrations (Alembic)
Currently using `Base.metadata.create_all()` on startup — this creates tables if they don't exist but will not modify existing tables if the schema changes. During early development, schema changes are handled by wiping the Docker postgres volume and letting the app recreate tables from scratch. Once the schema stabilizes, add **Alembic** for proper migration support (incremental, versioned schema changes — like git for the database).
