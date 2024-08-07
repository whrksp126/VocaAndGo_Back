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



db = SQLAlchemy()
migrate = Migrate()     
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
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
    
    with app.app_context():
        db.create_all()    
    from app.routes.login import login_bp
    from app.routes.search import search_bp
    from app.routes.tts import tts_bp
    
    app.register_blueprint(login_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(tts_bp)
    
    return app
