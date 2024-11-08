from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from flask_cors import CORS
import json
from datetime import datetime, timedelta

db = SQLAlchemy()
migrate = Migrate()     
login_manager = LoginManager()

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger 

import atexit
from pyfcm import FCMNotification


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


def send_fcm_message(app):
    with app.app_context():  # Flask 애플리케이션 컨텍스트 내에서 실행

        from app.models.models import db, User, UserHasToken, DailySentence

        today_kst = (datetime.utcnow() + timedelta(hours=9)).date()

        daily_sentence = db.session.query(DailySentence)\
                                    .filter(DailySentence.date == today_kst)\
                                    .first()

        # # 메시지 전송 API
        title = '오늘의 문장🌱 \n' + daily_sentence.sentence
        message = daily_sentence.meaning

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


def create_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: send_fcm_message(app), CronTrigger(hour=15, minute=43))
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    return scheduler




def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    CORS(app, supports_credentials=True)
    # CORS(app)

    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # login_manager.login_view = "main_login.html"
    
    # # 모든 모델 클래스들을 한번에 import
    from app.models import models
    from app.login_manager import load_user, unauthorized_callback
    
    from app.routes.login import login_bp
    from app.routes.search import search_bp
    from app.routes.tts import tts_bp
    from app.routes.fcm import fcm_bp
    from app.routes.drive import drive_bp
    from app.routes.mainpage import mainpage_bp
    
    app.register_blueprint(login_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(fcm_bp)
    app.register_blueprint(drive_bp)
    app.register_blueprint(mainpage_bp)

    # 애플리케이션 시작 시 스케줄러도 시작
    scheduler = create_scheduler(app)
    
    return app
