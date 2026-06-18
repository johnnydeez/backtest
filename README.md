# Backtest

A forex backtesting system built with FastAPI, Celery, Redis, and PostgreSQL.

## Stack

- **API:** FastAPI + Uvicorn
- **Job queue:** Celery + Redis
- **Database:** PostgreSQL (SQLAlchemy)
- **Data:** pandas, pandas-ta

## Starting the app

```bash
docker compose up
```

The app, worker, Redis, and Postgres all start together. Postgres has a healthcheck — the app and worker won't start until it's ready.

Verify the worker started correctly by checking its logs for this line:

```
[tasks]
  . app.tasks.backtest_task.run_backtest
```

## Restarting the worker after a code change

The worker does not hot-reload. After changing anything in `app/engine/` or `app/tasks/`:

```bash
docker compose restart worker
```

## Stopping

```bash
docker compose down
```

To also wipe the database (required for schema changes):

```bash
docker compose down -v
```

## Running a backtest

See [API.md](API.md) for the full request format and examples.
