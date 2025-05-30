# app/tasks.py
import logging
from celery import Celery
from .database import SessionLocal
from . import crud
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@app.task
def generate_monthly_report():
    logger.info("Oylik hisobot yaratilmoqda")
    db = SessionLocal()
    try:
        report = crud.get_monthly_summary_report(db)
        file_name = f"monthly_report_{datetime.utcnow().strftime('%Y_%m')}.json"
        logger.info(f"Hisobot fayli yaratilmoqda: {file_name}")
        with open(file_name, "w") as f:
            json.dump(report, f, indent=4)
        logger.info(f"Hisobot muvaffaqiyatli saqlandi: {file_name}")
        return report
    except Exception as e:
        logger.error(f"Hisobot yaratishda xato: {str(e)}")
        raise
    finally:
        db.close()