from flask import render_template, redirect, url_for, request, session, jsonify, send_file, send_from_directory
from app import db
from app.routes import tts_bp

from flask_login import current_user, login_required, login_user, logout_user

import json
from gtts import gTTS
import os
import uuid
import io


@tts_bp.route('/')
def tts():
    return render_template('tts_test.html')



# @tts_bp.route('/output', methods=['POST'])
@tts_bp.route('/output', methods=['GET'])
def tts_output():
    text = request.args.get('text')
    language = request.args.get('language')
    
    if not text:
        return jsonify({"error": "단어를 입력해주세요"}), 400
    
    # TTS 생성
    tts = gTTS(text=text, lang=language)
    
    # 저장 안하고 스트림으로 바로 보내장
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)  # Use write_to_fp instead of save
    mp3_fp.seek(0)  # Go to the start of the BytesIO object

    return send_file(mp3_fp, mimetype="audio/mp3", as_attachment=False, download_name="output.mp3")









# fcm test

from flask import Flask, request, jsonify

import firebase_admin
from firebase_admin import credentials, messaging


# fcm 서비스 계정 키 파일 경로
#cred = credentials.Certificate("app/config/vocaandgo-firebase-adminsdk-xyi9u-4a73c9d3d8.json")
#firebase_admin.initialize_app(cred)


@tts_bp.route('/fcm_html')
def fcm_html():
    return render_template('fcm3.html')


@tts_bp.route('/firebase-messaging-sw.js')
def firebase_messaging_sw():
    return send_from_directory('static', 'firebase-messaging-sw.js')


@tts_bp.route('/send_notification_test', methods=['POST'])
def send_notification_test():
    data = request.json
    token = data.get('token')
    message_body = data.get('message')

    # 메시지 구성
    message = messaging.Message(
        notification=messaging.Notification(
            title='Hello',
            body=message_body,
        ),
        token=token,
    )

    # 메시지 전송
    try:
        response = messaging.send(message)
        return jsonify({'success': True, 'message_id': response}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
import threading
@tts_bp.route('/get_token', methods=['POST'])
def get_token():
    # 인증된 사용자라면 사용자 ID 기반으로 토큰 생성
    user_id = request.json.get('user_id')
    registration_token = request.json.get('token')

    message = messaging.Message(
        notification=messaging.Notification(
            title='Hello!',
            body='This is a test message.'
        ),
        token=registration_token,
    )

    response = messaging.send(message)

    # 5초 후에 FCM 메시지를 보내기 위한 타이머 설정
    timer = threading.Timer(10.0, send_fcm, [message])
    timer.start()

    return jsonify({"status": "success", "response": response})

def send_fcm(message):
    # 실제로 FCM 메시지를 보내는 함수
    try:
        response = messaging.send(message)
        print("Successfully sent message:", response)
    except Exception as e:
        print("Error sending message:", e)





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

@tts_bp.route('/download_excel', methods=['GET'])
def download_excel():
    # BytesIO 객체를 사용하여 메모리에 엑셀 파일 생성
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # 각 단어장별로 시트를 생성
    for notebook in data:
        df = pd.DataFrame(notebook['words'], columns=['word', 'meaning', 'example'])
        df.columns = ['영단어', '한국어', '예문']
        df.to_excel(writer, sheet_name=notebook['name'], index=False)

    # writer 닫아서 파일 저장
    writer.close()
    output.seek(0)

    # 파일 전송
    return send_file(output, download_name='vocabularies.xlsx', as_attachment=True)


