from celery import Celery
import logging

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

def make_celery():
    celery = Celery(
        'tasks',
        broker = CELERY_BROKER_URL,
        backend = CELERY_RESULT_BACKEND
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
    logger.info('Successfully sent message:')