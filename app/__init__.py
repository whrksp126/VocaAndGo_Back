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

from app.login_manager import load_user, unauthorized_callback

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()



def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    CORS(app, supports_credentials=True)
    # CORS(app)

    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # login_manager.login_view = "main_login.html"

    login_manager.user_loader(load_user)
    login_manager.unauthorized_handler(unauthorized_callback)

    # # 모든 모델 클래스들을 한번에 import
    from app.models import models
    # from app.login_manager import load_user, unauthorized_callback
    
    from app.routes.login import login_bp
    from app.routes.search import search_bp
    from app.routes.tts import tts_bp
    from app.routes.fcm import fcm_bp
    from app.routes.drive import drive_bp
    from app.routes.mainpage import mainpage_bp
    # from app.routes.check import check_bp
    
    app.register_blueprint(login_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(fcm_bp)
    app.register_blueprint(drive_bp)
    app.register_blueprint(mainpage_bp)
    # app.register_blueprint(check_bp)

    # # 애플리케이션 시작 시 스케줄러도 시작
    # from app.routes.fcm import create_scheduler
    # scheduler = create_scheduler(app)
    
    return app
