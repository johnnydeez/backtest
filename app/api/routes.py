from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.database import SessionLocal
from app.db.models import BacktestJob
from app.tasks.backtest_task import run_backtest

router = APIRouter()


# TODO: a strict REST design would accept the strategy dict directly as the request body
# rather than wrapping it in {"strategy": {...}}. Revisit when adding Pydantic validation
# on the strategy schema itself.
class StrategyRequest(BaseModel):
    strategy: dict


@router.post("/backtest", status_code=202)
def submit_backtest(request: StrategyRequest):
    """
    Submit a strategy JSON to be backtested.
    Returns a job ID immediately — the backtest runs asynchronously.
    Poll GET /backtest/{job_id} for status and results.
    """
    db = SessionLocal()
    try:
        job = BacktestJob(params=request.strategy)
        db.add(job)
        db.commit()
        db.refresh(job)

        run_backtest.delay(job.id, request.strategy)

        return {"job_id": job.id}
    finally:
        db.close()


@router.get("/backtest/{job_id}")
def get_backtest(job_id: str):
    """
    Returns the status and results of a backtest job.
    Status values: pending, running, completed, failed.
    """
    db = SessionLocal()
    try:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "job_id": job.id,
            "status": job.status,
            "result_summary": job.result_summary,
            "result_file_path": job.result_file_path,
            "error": job.error,
            "created_at": job.created_at,
        }
    finally:
        db.close()
