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
cred = credentials.Certificate("app/config/vocaandgo-firebase-adminsdk-xyi9u-4a73c9d3d8.json")
firebase_admin.initialize_app(cred)


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
