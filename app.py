from app import create_app, db
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
# from app.init import start_scheduler

# login_manager = LoginManager()


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit


app = create_app()
migrate = Migrate(app, db)
# login_manager.init_app(app)
# login_manager.login_view = "main_login.html"
# CORS(app)


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


def send_fcm_message():
    with app.app_context():  # Flask 애플리케이션 컨텍스트 내에서 실행


        from app.models.models import db, User, UserHasToken

        print("1시에 FCM 메시지를 전송합니다.")
        # 여기에 FCM 메시지 전송 로직 작성

        # # 메시지 전송 API
        title = '두번쨰... 메시지'
        message = '잠온다'

        try:
            # # DB에서 저장된 토큰 조회
            # cursor.execute("SELECT token FROM fcm_tokens")
            # tokens = cursor.fetchall()

            tokens = db.session.query(UserHasToken).all()

            # 모든 토큰에 푸시 알림 전송
            results = []
            for token in tokens:
                try:
                    result = send_push_notification(title, message, token.token)
                    results.append(result)
                except Exception as e:
                    print(f"Error sending to token {token.token}: {e}")
                    results.append({"error": str(e), "token": token.token})

            print("fcm success!")
            return json.dumps({"results": results}), 200
        except Exception as e:
            print("fcm failed : ", e)
            return json.dumps({"error": str(e)}), 500


def create_scheduler():
    print('!!!!!!!!!!!!!')
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_fcm_message, IntervalTrigger(minutes=1))  # 매 1분마다 실행
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    return scheduler

# 애플리케이션 시작 시 스케줄러도 시작
scheduler = create_scheduler()

print('?@?@?@?@')

if __name__ == '__main__':
    # start_scheduler()
    app.run(debug=True)