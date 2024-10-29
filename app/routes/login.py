from flask import render_template, redirect, url_for, request, session, jsonify
from app import db
from app.routes import login_bp
from app.models.models import User

from flask_login import current_user, login_required, login_user, logout_user
import requests

import json
from werkzeug.security import generate_password_hash, check_password_hash

import io
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload, MediaIoBaseDownload
from urllib.parse import urlencode

from requests_oauthlib import OAuth2Session
from config import OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI


@login_bp.route('/')
@login_required
def index():
    return render_template('main_login.html')


# 로그인 라우트: 구글 OAuth2 인증 요청
@login_bp.route('/google')
def login_google():
    device_type = request.args.get('device_type', 'web')
    session['device_type'] = device_type
    # OAuth2Session 생성
    oauth = OAuth2Session(OAUTH_CLIENT_ID, redirect_uri=OAUTH_REDIRECT_URI, 
                          scope=[
                              'https://www.googleapis.com/auth/userinfo.profile', 
                              'https://www.googleapis.com/auth/userinfo.email', 
                              'openid',
                              'https://www.googleapis.com/auth/drive.file'
                            ]
                        )

    # 인증 요청을 생성합니다.
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        access_type="offline",
        prompt="consent"
    )

    # 상태(state)를 세션에 저장
    session['oauth_state'] = state

    return redirect(authorization_url)


# 인증 콜백 라우트: OAuth2 인증 완료 후 실행
@login_bp.route('/login_google/callback')
def authorize_google():
    # 상태(state)를 가져옴
    state = session.pop('oauth_state', None)
    # 사용자가 리디렉션된 후에 받은 정보를 가져옵니다.
    authorization_response = request.url
    if state is None or state != request.args.get('state'):
        return 'Invalid OAuth state', 400
    # 사용자가 인증을 마치고 리디렉션 된 후, 코드를 얻어서 토큰을 교환합니다.
    oauth = OAuth2Session(OAUTH_CLIENT_ID, redirect_uri=OAUTH_REDIRECT_URI, state=state, 
                          scope=[
                                'https://www.googleapis.com/auth/userinfo.profile',
                                'https://www.googleapis.com/auth/userinfo.email',
                                'openid',
                                'https://www.googleapis.com/auth/drive.file'
                              ]
                        )
    try:
        token = oauth.fetch_token(
            'https://accounts.google.com/o/oauth2/token',
            authorization_response=authorization_response,
            client_secret=OAUTH_CLIENT_SECRET
        )
        # 토큰에서 사용자 정보 추출
        userinfo = oauth.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
    except Exception as e:
        print(f"Error during token fetch or userinfo fetch: {str(e)}")
        return f"An error occurred: {str(e)}", 500
    # 토큰 정보를 세션에 저장
    session['token'] = token
    # 사용자 정보 확인
    user = User.query.filter_by(google_id=userinfo['id']).first()
    if user is None:
        # 사용자가 존재하지 않으면 회원가입 처리
        new_user = User(
            email=userinfo['email'],
            google_id=userinfo['id'],
            name=userinfo.get('name', ''),
            phone=None
        )
        db.session.add(new_user)
        db.session.commit()
        user = new_user

    # 사용자 정보를 세션에 저장
    session['user_id'] = user.id
    login_user(user)
    front_end_url = 'https://voca.ghmate.com/html/login.html'
    query_params = {
        'token': token['access_token'],
        'email': user.email,
        'name': user.name,
        'type': 'web',
        'status': 200
    }
    redirect_url = f"{front_end_url}?{urlencode(query_params)}"
    return redirect(redirect_url)

    # # return jsonify({'name': user.name, 'email': user.email}), 200

# 웹뷰앱 로그인 처리
@login_bp.route('/login_google/callback/app', methods=['POST'])
def authorize_google():
    data = request.json
    google_id = data.get('googleId')
    access_token = data.get('accessToken')
    refresh_token = data.get('refreshToken')
    email = data.get('email')
    name = data.get('name')

    # 토큰 정보를 세션에 저장
    session['token'] = access_token
    # 사용자 정보 확인
    user = User.query.filter_by(google_id=google_id).first()
    if user is None:
        # 사용자가 존재하지 않으면 회원가입 처리
        user = User(
            email = email,
            google_id = google_id,
            name = name,
            phone = None,
            refresh_token = refresh_token
        )
        db.session.add(user)
    else:
        user.refresh_token = refresh_token  # 새로운 refresh_token으로 갱신
    db.session.commit()
    # 사용자 정보를 세션에 저장
    session['user_id'] = user.id

    return jsonify({ 'code' : 200, 'status': 'success'})

# 토큰 갱신 함수
def refresh_access_token(user):
    refresh_token = user.refresh_token
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        'client_id': OAUTH_CLIENT_ID,
        'client_secret': OAUTH_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(token_url, data=data)
    if response.ok:
        new_access_token = response.json().get('access_token')
        session['access_token'] = new_access_token
        return new_access_token
    return None


@login_bp.route("/logout")
@login_required
def logout():
    session.pop('token', None)
    session.pop('user_id', None)
    logout_user()
    return render_template('index.html')
