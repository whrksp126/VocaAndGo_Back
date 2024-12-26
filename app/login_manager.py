# from flask import session, jsonify, request, render_template, request
# from flask_login import LoginManager, UserMixin, login_required

# from app.models.models import db, User

from app import login_manager # Flask-login의 변수

# # 사용자 로드 함수
# @login_manager.user_loader
# def load_user(user_id):
#     print("@#$load_user")
#     user_item = db.session.query(User).filter(User.id == user_id).first()
#     return user_item

# # 로그인이 되어있지 않은 경우
# @login_manager.unauthorized_handler
# def unauthorized_callback():
#     print("@#$unauthorized")
#     print('로그인이 되어있지 않은 경우')
#     return render_template('main_login.html')



# # 사용자 로드 함수
# @login_manager.user_loader
# def load_user(user_id):
#     from app.models.models import db, User
    
#     print("@#$load_user")
#     user_item = db.session.query(User).filter(User.id == user_id).first()
#     return user_item

# # 로그인이 되어있지 않은 경우
# @login_manager.unauthorized_handler
# def unauthorized_callback():
#     print("@#$unauthorized")
#     print('로그인이 되어있지 않은 경우')
#     return "로그인이 필요합니다.", 401
