# from flask import session, jsonify, request, render_template, request
# from flask_login import LoginManager, UserMixin, login_required

# from app import login_manager, db
# from app.models.models import User


# # 사용자 로드 함수
# @login_manager.user_loader
# def load_user(user_id):
#     user_item = db.session.query(User).filter(User.id == user_id).first()
#     return user_item

# # 로그인이 되어있지 않은 경우
# @login_manager.unauthorized_handler
# def unauthorized_callback():
#     print('로그인이 되어있지 않은 경우')
#     return render_template('login.html')


# # # 유저 세선 등록
# # def update_user_session(user_item):
# #     session['user_item'] = user_item
# #     return jsonify({'message': '유저 세션 등록 성공'}), 200
