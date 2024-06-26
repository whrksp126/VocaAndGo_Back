from flask import session, jsonify, request, render_template, request
from flask_login import LoginManager, UserMixin, login_required

from app.models.models import db, User

from app import login_manager # Flask-login의 변수


# 사용자 로드 함수
@login_manager.user_loader
def load_user(user):
    user_item = db.session.query(User).filter(User.id == user.id).first()
    return user_item

# 로그인이 되어있지 않은 경우
@login_manager.unauthorized_handler
def unauthorized_callback():
    print('로그인이 되어있지 않은 경우')
    return render_template('login.html')

