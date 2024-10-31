from flask import render_template, redirect, url_for, request, session, jsonify
from app import db
from app.routes import drive_bp
from app.models.models import User


from flask_login import current_user, login_required, login_user, logout_user
import json
from werkzeug.security import generate_password_hash, check_password_hash

import io
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request

from urllib.parse import urlencode

from requests_oauthlib import OAuth2Session
from config import OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI, OAUTH_ANDROID_PRODUCTION_CLIENT_ID, OAUTH_ANDROID_PLAY_STORE_CLIENT_ID


###### 엑셀 테스트 ######

from flask import send_file
import pandas as pd
from io import BytesIO

# 더미 데이터
data = [
    {
        "name":"기본 단어장",
        "color":{"main":"CD8DFF","background":"F6EFFF"},
        "createdAt":"2024-09-04T18:17:18.716Z",
        "updatedAt":"2024-09-04T18:17:18.716Z",
        "status":"active",
        "id":1,
        "words":[
            {
                "notebookId":1,
                "word":"tell",
                "meaning":["말하다","이야기하다"],
                "example":[
                    {
                        "origin":"tell a good joke",
                        "meaning":"재치 있는 농담을 하다"
                    },
                    {
                        "origin":"tell him a story",
                        "meaning":"그에게 이야기를 들려주다"
                    }
                ],
                "description":"",
                "createdAt":"2024-09-04T18:17:28.026Z",
                "updatedAt":"2024-09-04T18:17:28.026Z",
                "status":0,
                "id":1
            },
            {"notebookId":1,"word":"hidden","meaning":["숨은","감춰진","비밀의","남모르게"],"example":[{"origin":"a hidden tax","meaning":"간접세(indirect tax)"},{"origin":"a hidden microphone","meaning":"숨겨진 마이크"}],"description":"","createdAt":"2024-09-04T18:31:47.497Z","updatedAt":"2024-09-04T18:31:47.497Z","status":0,"id":2},
            {"notebookId":1,"word":"big","meaning":["큰","중요한","많이","대단한"],"example":[{"origin":"a big tree","meaning":"큰 나무[집](※a great oak 커다란 참나무)"},{"origin":"a big city","meaning":"대도시"}],"description":"","createdAt":"2024-09-04T18:31:54.984Z","updatedAt":"2024-09-04T18:31:54.984Z","status":0,"id":3},
            {"notebookId":1,"word":"giant","meaning":["거대한","자이언트","거인","위대한"],"example":[{"origin":"an economic giant","meaning":"경제 대국"},{"origin":"a musical giant","meaning":"위대한 음악가"}],"description":"","createdAt":"2024-09-04T18:32:29.489Z","updatedAt":"2024-09-04T18:32:29.489Z","status":0,"id":4}
        ]
    },
    {
        "name":"고급 단어장",
        "color":{"main":"FF8DD4","background":"FFEFFA"},
        "createdAt":"2024-09-04T18:33:01.160Z",
        "updatedAt":"2024-09-04T18:33:01.160Z",
        "status":"active",
        "id":2,
        "words":[
            {"notebookId":2,"word":"peaceful","meaning":["평화적인","평화로운","편안한"],"example":[{"origin":"peaceful times","meaning":"태평 세월"},{"origin":"a peaceful death","meaning":"평온한 죽음[임종]"}],"description":"","createdAt":"2024-09-04T18:33:10.409Z","updatedAt":"2024-09-04T18:33:10.409Z","status":0,"id":5},
            {"notebookId":2,"word":"quotient","meaning":["상","몫","할당"],"example":[{"origin":"an intelligence quotient","meaning":"지능지수(약자: IQ)."},{"origin":"emotional quotient ","meaning":"감성 지수(약자: EQ)."}],"description":"","createdAt":"2024-09-04T18:33:26.631Z","updatedAt":"2024-09-04T18:33:26.631Z","status":0,"id":6},
            {"notebookId":2,"word":"political","meaning":["정치의","정계의","정당의","정략의"],"example":[{"origin":"political theory","meaning":"정치학 이론"},{"origin":"a political animal","meaning":"(아리스토텔레스가 말한) 정치적 동물(※인간에 대한 정의); 타고난 정치가"}],"description":"","createdAt":"2024-09-04T18:33:32.730Z","updatedAt":"2024-09-04T18:33:32.730Z","status":0,"id":7}
        ]
    }
]


# TODO : word->origin
@drive_bp.route('/download_excel', methods=['GET'])
def download_excel():
    # BytesIO 객체를 사용하여 메모리에 엑셀 파일 생성
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # 각 단어장별로 시트를 생성
    for notebook in data:
            # DataFrame 생성
            df = pd.DataFrame(notebook['words'], columns=['word', 'meaning', 'example'])

            # 'meaning' 열의 리스트를 쉼표로 구분된 문자열로 변환
            df['meaning'] = df['meaning'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

            # 'example' 열도 필요한 경우 같은 방식으로 처리
            df['example'] = df['example'].apply(lambda x: '|\n'.join(x) if isinstance(x, list) else x)

            # DataFrame을 엑셀 시트에 저장
            df.to_excel(writer, sheet_name=notebook['name'], index=False)

    # writer 닫아서 파일 저장
    writer.close()
    output.seek(0)

    # 파일 전송
    return send_file(output, download_name='vocabularies.xlsx', as_attachment=True)


# ### 드라이브에 json으로 저장 TODO : vocaandgo폴더 안에 저장시키기
# @drive_bp.route('/backup')
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
@drive_bp.route('/backup', methods=['POST'])
@login_required
def backup():
    print("ckeck_backup")
    data = request.get_json()
    if not data:
        return jsonify({"code":400, "msg": "제공된 데이터가 없습니다"})
    drive_service = None
    user = User.query.filter_by(google_id=session['user_id']).first()
    if session['os'] == 'web' :
        credentials = Credentials(
            token=session['access_token'],
            refresh_token=user.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET
        )
        drive_service = build('drive', 'v3', credentials=credentials)
    elif session['os'] == 'android':
        print('#### android')
        credentials = Credentials(token=session['access_token'])
        drive_service = build('drive', 'v3', credentials=credentials)
    
    
    # 폴더 이름
    folder_name = 'HeyVoca'

    # # 폴더가 존재하는지 확인
    # query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    # results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    # folders = results.get('files', [])

    folders = None
    # 폴더 존재 확인 로깅
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    try:
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])
        print(f"폴더 조회 결과: {folders}")
    except Exception as e:
        print("폴더 조회 중 오류 발생:", e)
        return jsonify({"code": 500, "msg": "Google Drive 폴더 조회 실패"})
    print('#### 지나옴')


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
    # output = io.BytesIO()
    # writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # for notebook in data:
    #         # DataFrame 생성
    #         df = pd.DataFrame(notebook['words'], columns=['word', 'meaning', 'example'])

    #         # 'meaning' 열의 리스트를 쉼표로 구분된 문자열로 변환
    #         df['meaning'] = df['meaning'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

    #         # 'example' 열도 필요한 경우 같은 방식으로 처리
    #         df['example'] = df['example'].apply(lambda x: '|\n'.join(x) if isinstance(x, list) else x)

    #         # DataFrame을 엑셀 시트에 저장
    #         df.to_excel(writer, sheet_name=notebook['name'], index=False)

    # writer.close()
    # output.seek(0)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for notebook in data:
            sheet_name = notebook['name']
            words = notebook['words']

            # 노트북의 메타데이터를 DataFrame으로 저장
            metadata = pd.DataFrame([{
                "name": notebook['name'],
                "color_main": notebook['color']['main'],
                "color_background": notebook['color']['background'],
                "createdAt": notebook['createdAt'],
                "updatedAt": notebook['updatedAt'],
                "status": notebook['status'],
                "id": notebook['id']
            }])

            # 메타데이터를 시트에 먼저 저장
            metadata.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

            # 단어 데이터 추가
            if words:
                df_words = pd.DataFrame(words)
                df_words.to_excel(writer, sheet_name=sheet_name, index=False, startrow=len(metadata) + 2)
            else:
                pd.DataFrame().to_excel(writer, sheet_name=sheet_name, index=False, startrow=len(metadata) + 2)

    output.seek(0)
    print('#### 3333')
    # Google Drive에 엑셀 파일 업로드
    file_metadata = {
        'name': 'heyvoca_backup.xlsx',
        'parents': [folder_id]  # 파일을 업로드할 폴더 지정
    }
    print('#### 4444')
    media = MediaIoBaseUpload(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    print('#### 5555')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('#### 6666')
    return jsonify({"code": 200})


@drive_bp.route('/excel_to_json', methods=['GET'])
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

    # 'HeyVoca' 폴더 검색
    folder_name = 'HeyVoca'
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = results.get('files', [])

    if not folders:
        return jsonify({"code":404, "msg": "백업 폴더가 없습니다"})

    folder_id = folders[0]['id']

    # 폴더에서 'heyvoca_backup.xlsx' 파일 검색
    query = f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and name='heyvoca_backup.xlsx' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        return jsonify({"code":404, "msg": "백업 파일이 없습니다"})

    file_id = files[0]['id']

    # 엑셀 파일 다운로드
    request = drive_service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)

    # 엑셀 파일을 읽어 JSON으로 변환
    restored_data = []
    with pd.ExcelFile(fh) as xls:
        for sheet_name in xls.sheet_names:
            # 시트별로 데이터 읽기
            metadata = pd.read_excel(xls, sheet_name=sheet_name, skiprows=0, nrows=1).to_dict(orient='records')[0]
            words = pd.read_excel(xls, sheet_name=sheet_name, skiprows=3).fillna('').to_dict(orient='records')

            # words 데이터 내 example과 meaning을 JSON으로 변환
            for word in words:
                # example, meaning 필드가 JSON 문자열이라면 리스트로 변환
                if 'example' in word and isinstance(word['example'], str):
                    try:
                        word['example'] = json.loads(word['example'])
                    except json.JSONDecodeError:
                        word['example'] = [word['example']]  # JSON 파싱 실패 시 문자열 그대로 리스트에 넣음

                if 'meaning' in word and isinstance(word['meaning'], str):
                    try:
                        word['meaning'] = json.loads(word['meaning'])
                    except json.JSONDecodeError:
                        word['meaning'] = [word['meaning']]  # JSON 파싱 실패 시 문자열 그대로 리스트에 넣음

            # JSON 데이터 구조 복원
            notebook = {
                "name": metadata["name"],
                "color": {
                    "main": metadata["color_main"],
                    "background": metadata["color_background"]
                },
                "createdAt": metadata["createdAt"],
                "updatedAt": metadata["updatedAt"],
                "status": metadata["status"],
                "id": metadata["id"],
                "words": words  # words 데이터를 수정된 형태로 추가
            }

            restored_data.append(notebook)

    print("restore_data", restored_data)
    return jsonify({"code":200, "data": restored_data})