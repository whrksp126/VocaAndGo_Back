from celery import Celery
from celery.schedules import crontab, timedelta
import logging
import os

from app import create_app
from app.routes.fcm import send_notification

# Celery 설정
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

def make_celery():
    celery = Celery(
        'tasks',
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND
    )
    celery.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        result_expires=3600
    )
    return celery

celery = make_celery()

# 로깅 설정
logging.basicConfig(filename='celery.log', level=logging.INFO)
logger = logging.getLogger(__name__)


# Celery 작업 정의
@celery.task
def send_fcm_message():
    app = create_app()
    with app.app_context():
        send_notification()     # fcm 함수 실행


# Celery Beat 스케줄 설정
celery.conf.beat_schedule = {
    'send-fcm-every-10-seconds': {
        'task': 'app.celery_worker_beat.send_fcm_message',
        'schedule': crontab(minute='*/1')
        # 'schedule': crontab(hour=13, minute=0, day_of_week='*') # KST 22:00
    },
}
celery.conf.timezone = 'UTC'

def main():
    if len(os.sys.argv) > 1 and os.sys.argv[1] == 'beat':
        # Celery Beat 실행
        celery.start(argv=['celery', 'beat', '--loglevel=info'])
    else:
        # Celery Worker 실행
        celery.start(argv=['celery', 'worker', '--loglevel=info'])

if __name__ == '__main__':
    main()
