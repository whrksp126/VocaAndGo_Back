from celery import Celery
from celery.schedules import crontab, timedelta
from celery import Celery
from celery_config import celery

# Celery 비트 스케줄 설정
# celery.conf.beat_schedule = {
#     'send-fcm-every-day-at-8am': {
#         'task': 'celery.send_fcm_message',
#         'schedule': crontab(hour=8, minute=0),  # 매일 오전 08:00
#     },
# }
celery.conf.beat_schedule = {
    'send-fcm-every-10-seconds': {
        'task': 'celery.send_fcm_message',
        'schedule': timedelta(seconds=10),  # 10초마다 실행
    },
}
celery.conf.timezone = 'UTC'

if __name__ == '__main__':
    celery.start()
