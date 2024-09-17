from flask import render_template, redirect, url_for, request, session, jsonify
from app import db
from app.routes import login_bp
from app.models.models import User

from flask_login import current_user, login_required, login_user, logout_user

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

    # type 값을 세션에서 가져옴
    device_type = session.pop('device_type', 'web')

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


    # type에 따른 리디렉션 URL 생성
    if device_type == 'web':
        front_end_url = 'https://voca.ghmate.com/html/login.html'
        query_params = {
            'token': token['access_token'],
            'email': user.email,
            'name': user.name,
            'status': 200
        }
        redirect_url = f"{front_end_url}?{urlencode(query_params)}"
        print('####################################33')
        print(f"Redirect URL: {redirect_url}")
        return redirect(redirect_url)
    elif device_type == 'app':
        # Expo 앱으로 리디렉션 URL 생성
        # 프로덕션 앱으로 리디렉션 URL 생성
        # app_redirect_url = 'vocaandgo_app://auth'
        # app_redirect_url = 'https://voca.ghmate.com/html/login.html'
        # app_redirect_url = 'exp://192.168.1.16:8081/--/auth'
        app_redirect_url = 'HeyVoca://auth'

        query_params = {
            'token': token['access_token'],
            'email': user.email,
            'name': user.name,
            'status': 200
        }
        redirect_url = f"{app_redirect_url}?{urlencode(query_params)}"
        print('####################################33')
        print(f"Redirect URL: {redirect_url}")

        return redirect(redirect_url)
    else:
        return 'Invalid auth type', 400

    # # return jsonify({'name': user.name, 'email': user.email}), 200




@login_bp.route("/logout")
@login_required
def logout():
    session.pop('token', None)
    session.pop('user_id', None)
    logout_user()
    return render_template('index.html')


# ### 드라이브에 json으로 저장 TODO : vocaandgo폴더 안에 저장시키기
# @login_bp.route('/backup')
# @login_required
# def backup():
#     # if 'credentials' not in session:
#         # return redirect(url_for('login'))


#     # token에서 Credentials 객체 생성
#     token = session['token']
#     credentials = Credentials(
#         token=token['access_token'],
#         refresh_token=token.get('refresh_token'),
#         token_uri='https://oauth2.googleapis.com/token',
#         client_id=OAUTH_CLIENT_ID,
#         client_secret=OAUTH_CLIENT_SECRET
#     )
    
#     drive_service = build('drive', 'v3', credentials=credentials)

#     # 폴더 이름
#     folder_name = 'vocaandgo'
    
#     # 폴더가 존재하는지 확인
#     query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
#     results = drive_service.files().list(q=query, fields="files(id, name)").execute()
#     folders = results.get('files', [])

#     if not folders:
#         # 폴더가 없으면 생성
#         file_metadata = {
#             'name': folder_name,
#             'mimeType': 'application/vnd.google-apps.folder'
#         }
#         folder = drive_service.files().create(body=file_metadata, fields='id').execute()
#         folder_id = folder.get('id')
#     else:
#         # 폴더가 있으면 그 폴더 ID 사용
#         folder_id = folders[0].get('id')
    
#     # JSON 데이터를 메모리 스트림으로 변환
#     json_data = {
#         "example_key": "example_value",
#         "another_key": 12345
#     }
#     json_str = json.dumps(json_data)
#     json_bytes = io.BytesIO(json_str.encode('utf-8'))
    
#     file_metadata = {
#         'name': 'wordlist_backup.json',
#         'parents': [folder_id]
#     }
#     media = MediaIoBaseUpload(json_bytes, mimetype='application/json')
#     file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
#     return jsonify({"file_id": file.get('id')})


## 드라이브에 엑셀 파일로 저장 TODO : word->origin
from flask import send_file
import pandas as pd
from io import BytesIO
from app.routes.tts import data
@login_bp.route('/backup')
@login_required
def backup():
    data = request.get_json()
    if not data:
        return jsonify({"error": "제공된 데이터가 없습니다"}), 400
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

    # 폴더 이름
    folder_name = 'HeyVoca'
    
    # 폴더가 존재하는지 확인
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])

    if not folders:
        # 폴더가 없으면 생성
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
    else:
        # 폴더가 있으면 그 폴더 ID 사용
        folder_id = folders[0].get('id')

    # 엑셀 파일 생성
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    for notebook in data:
            # DataFrame 생성
            df = pd.DataFrame(notebook['words'], columns=['word', 'meaning', 'example'])

            # 'meaning' 열의 리스트를 쉼표로 구분된 문자열로 변환
            df['meaning'] = df['meaning'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

            # 'example' 열도 필요한 경우 같은 방식으로 처리
            df['example'] = df['example'].apply(lambda x: '|\n'.join(x) if isinstance(x, list) else x)

            # DataFrame을 엑셀 시트에 저장
            df.to_excel(writer, sheet_name=notebook['name'], index=False)

    writer.close()
    output.seek(0)

    # Google Drive에 엑셀 파일 업로드
    file_metadata = {
        'name': 'vocabularies_backup.xlsx',
        'parents': [folder_id]  # 파일을 업로드할 폴더 지정
    }
    media = MediaIoBaseUpload(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    return jsonify({"file_id": file.get('id')})


@login_bp.route('/excel_to_json')
@login_required
def excel_to_json():
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

    # 파일 이름
    file_name = 'vocabularies_backup.xlsx'
    
    # Google Drive에서 파일 검색
    query = f"name='{file_name}' and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        return jsonify({"error": "File not found"}), 404

    file_id = files[0]['id']

    # 파일 다운로드
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    # 파일의 내용을 읽음
    fh.seek(0)
    excel_data = pd.ExcelFile(fh)

    # 데이터를 저장할 리스트
    data = []

    # 각 시트를 순회
    for sheet_name in excel_data.sheet_names:
        # 시트 읽기
        df = pd.read_excel(excel_data, sheet_name=sheet_name)

        # 'meaning'과 'example'을 리스트로 변환
        df['meaning'] = df['meaning'].apply(lambda x: x.split(', ') if isinstance(x, str) else x)
        df['example'] = df['example'].apply(lambda x: x.split('|\n') if isinstance(x, str) else x)

        # 필요한 데이터를 JSON 형태로 변환
        notebook = {
            'name': sheet_name,
            'words': df.to_dict(orient='records')  # 각 행을 딕셔너리 형태로 변환
        }
        
        data.append(notebook)

    print("data",data)
    return jsonify(data)
