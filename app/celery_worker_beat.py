from celery import Celery
from celery.schedules import crontab, timedelta
import logging
import os


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



from pyfcm import FCMNotification
from app import db
from app.models.models import db, User, UserHasToken
import json

# FCM API 키 (Firebase Console에서 확인 가능)
push_service = FCMNotification(service_account_file='app/config/vocaandgo-firebase-adminsdk-xyi9u-e4f0ccc423.json',
                                 project_id='vocaandgo')


# FCM 메시지 전송 함수
def send_push_notification(title, message, token):
    result = push_service.notify(fcm_token=token, 
                                notification_title=title, 
                                notification_body=message, 
                                notification_image=None
                            )

    return result


# 메시지 전송 API
def send_notification():
    # title = request.json.get('title')
    # message = request.json.get('message')
    title = '팀이 꼭...(더보기)'
    message = '팀이 꼭 이 메시지를 봤으면 좋겠다...'

    try:
        # # DB에서 저장된 토큰 조회
        # cursor.execute("SELECT token FROM fcm_tokens")
        # tokens = cursor.fetchall()

        tokens = db.session.query(UserHasToken).all()

        # 모든 토큰에 푸시 알림 전송
        results = []
        for token in tokens:
            result = send_push_notification(title, message, token.token)
            results.append(result)

        print("fcm success!")
        return json.dumps({"results": results}), 200
    except Exception as e:
        print("fcm failed : ", e)
        return json.dumps({"error": str(e)}), 500


# Celery 작업 정의
@celery.task
def send_fcm_message():
    send_notification()     # fcm 함수 실행
    logger.info('Successfully sent message:')

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
