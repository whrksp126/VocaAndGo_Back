from flask import render_template, redirect, url_for, request
from requests_oauthlib import OAuth2Session

from config import CLIENT_ID, REDIRECT_URI, CLIENT_SECRET
from app.routes import login_bp


@login_bp.route('/')
def index():
    return render_template('login.html')


# 로그인 라우트: 구글 OAuth2 인증 요청
@login_bp.route('/login/google')
def login_google():
    # OAuth2Session 생성
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['openid', 'email', 'profile'])

    # 인증 요청을 생성합니다.
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
    )
    return redirect(authorization_url)


# 인증 콜백 라우트: OAuth2 인증 완료 후 실행
@login_bp.route('/login/google/callback')
def authorize_google():
    # OAuth2Session 생성
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=['openid', 'email', 'profile'])

    # 인증 요청을 생성합니다.
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
    )

    # 사용자에게 인증을 받기 위해 authorization_url로 리다이렉트합니다.
    print('Please go to %s and authorize access.' % authorization_url)

    # 사용자가 리디렉션된 후에 받은 정보를 가져옵니다.
    authorization_response = request.url

    # 사용자가 인증을 마치고 리디렉션 된 후, 코드를 얻어서 토큰을 교환합니다.
    token = oauth.fetch_token(
        'https://accounts.google.com/o/oauth2/token',
        authorization_response=authorization_response,
        client_secret=CLIENT_SECRET
    )

    print(token)