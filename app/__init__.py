# from flask import Flask
# from config import Config
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# # from flask_login import LoginManager

# from sqlalchemy.ext.declarative import declarative_base
# from contextlib import contextmanager
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import create_engine, text

# # db = SQLAlchemy()
# # migrate = Migrate()     
# # login_manager = LoginManager()

# def create_app():
#     app = Flask(__name__)
#     # app.config.from_object(Config)
    
#     # db.init_app(app)
#     # migrate.init_app(app, db)
#     # login_manager.init_app(app)
    
#     # 모든 모델 클래스들을 한번에 import
#     # from app import models
    
#     # with app.app_context():
#         # db.create_all()    
        
#     # from app.routes.login import login_bp
    
#     # app.register_blueprint(login_bp)
    
#     return app

from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return 'Hello, World!'

    return app