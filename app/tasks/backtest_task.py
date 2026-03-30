import json
import os
import traceback
from app.worker import celery_app
from app.db.database import SessionLocal
from app.db.models import BacktestJob
from app.engine.params import BacktestParams
from app.engine.state import TestState
from app.engine.loop import BacktestLoop


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


@celery_app.task
def run_backtest(job_id: str, strategy: dict):
    db = SessionLocal()
    try:
        job = db.get(BacktestJob, job_id)
        job.status = "running"
        db.commit()

        params = BacktestParams(strategy)
        state = TestState()
        loop = BacktestLoop(params, state)
        loop.run()

        summary = _build_summary(state)
        detail_path = _save_detail(job_id, state)

        job.result_summary = summary
        job.result_file_path = detail_path
        job.status = "completed"
        db.commit()

    except Exception as e:
        job.status = "failed"
        job.error = traceback.format_exc()
        db.commit()
        raise e
    finally:
        db.close()


def _build_summary(state: TestState) -> dict:
    trades = state.closed_trades
    total_trades = len(trades)
    winners = [t for t in trades if t["dollar_profit"] > 0]
    win_rate = (len(winners) / total_trades * 100) if total_trades > 0 else 0
    total_return = state.balance - state.initial_balance

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_return": round(total_return, 2),
        "final_balance": round(state.balance, 2),
        "max_drawdown": round(state.max_drawdown, 2),
    }


def _save_detail(job_id: str, state: TestState) -> str:
    detail = {
        "closed_trades": state.closed_trades,
    }
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    with open(path, "w") as f:
        json.dump(detail, f, indent=2, default=str)
    return path
