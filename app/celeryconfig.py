from celery.schedules import crontab

beat_schedule = {
    'generate-monthly-report': {
        'task': 'app.tasks.generate_monthly_report',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # Har oy 1-kuni
    },
    'update-portion-estimations': {
        'task': 'app.tasks.update_portion_estimations',
        'schedule': crontab(minute=0, hour='*'),  # Har soatda
    },
}