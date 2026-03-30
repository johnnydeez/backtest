import os
from celery import Celery

REDIS_URL = os.environ["REDIS_URL"]

celery_app = Celery("backtest", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.include = ["app.tasks.backtest_task"]
