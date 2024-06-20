from flask import render_template, redirect, url_for, request, session, jsonify
from app.routes import login_bp
# from app.models import User

# from flask_login import current_user, login_required, login_user

import json


import io
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload, MediaIoBaseDownload

from requests_oauthlib import OAuth2Session
from config import OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI


@login_bp.route('/')
def index():
    return render_template('/main_login.html')


# 로그인 라우트: 구글 OAuth2 인증 요청
@login_bp.route('/login/google')
def login_google():
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

    # 사용자가 인증을 마치고 리디렉션 된 후, 코드를 얻어서 토큰을 교환합니다.
    oauth = OAuth2Session(OAUTH_CLIENT_ID, redirect_uri=OAUTH_REDIRECT_URI, state=state, 
                          scope=[
                                'https://www.googleapis.com/auth/userinfo.profile',
                                'https://www.googleapis.com/auth/userinfo.email',
                                'openid',
                                'https://www.googleapis.com/auth/drive.file'
                              ]
                        )

    # 상태(state) 확인
    if state is None or state != request.args.get('state'):
        return 'Invalid OAuth state', 400

    token = oauth.fetch_token(
        'https://accounts.google.com/o/oauth2/token',
        authorization_response=authorization_response,
        client_secret=OAUTH_CLIENT_SECRET
    )
    print("@@@token", token)

    # 토큰에서 사용자 정보 추출
    userinfo = oauth.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
    print("@@@userinfo", userinfo)

    # 토큰 정보를 세션에 저장
    session['token'] = token







    # # 사용자 정보 확인
    # user = User.query.filter_by(google_id=userinfo['id']).first()
    
    # if user is None:
    #     print("comming!!!")
    #     print("userinfo", userinfo['id'])
    #     # 사용자가 존재하지 않으면 회원가입 처리
    #     new_user = User(
    #         email=userinfo['email'],
    #         name=userinfo.get('name', ''),
    #         google_id=userinfo['id']
    #     )
    #     session.add(new_user)
    #     session.commit()
    #     user = new_user

    # # 사용자 정보를 세션에 저장
    # session['user_id'] = user.id






    return "Authentication Successful!"


@login_bp.route('/backup')
def backup():
    # if 'credentials' not in session:
        # return redirect(url_for('login'))


    # token에서 Credentials 객체 생성
    token = session['token']
    credentials = Credentials(
        token=token['access_token'],
        refresh_token=token.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=OAUTH_CLIENT_ID,
        client_secret=OAUTH_CLIENT_SECRET
    )
    
    drive_service = build('drive', 'v3', credentials=credentials)
    

    # JSON 데이터를 메모리 스트림으로 변환
    json_data = {
        "example_key": "example_value",
        "another_key": 12345
    }
    json_str = json.dumps(json_data)
    json_bytes = io.BytesIO(json_str.encode('utf-8'))
    
    file_metadata = {'name': 'wordlist_backup.json'}
    media = MediaIoBaseUpload(json_bytes, mimetype='application/json')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    return jsonify({"file_id": file.get('id')})