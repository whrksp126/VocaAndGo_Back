from flask import render_template, redirect, url_for, request, session, jsonify, send_file
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



@tts_bp.route('/output', methods=['POST'])
def tts_output():
    data = request.json
    text = data.get('text')
    language = data.get('language', 'en')
    
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
cred = credentials.Certificate("app/config/heyvoca-firebase-adminsdk-buwfz-bbbe06268c.json")
firebase_admin.initialize_app(cred)


@tts_bp.route('/fcm_html')
def fcm_html():
    return render_template('fcm.html')

@tts_bp.route('/send_notification', methods=['POST'])
def send_notification():
    try:
        # 클라이언트로부터 토큰과 메시지를 받음
        token = request.json.get('token')
        title = request.json.get('title')
        body = request.json.get('body')
        
        # FCM 메시지 생성
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )

        # 메시지 전송
        response = messaging.send(message)
        print("@#$@#$@#$response", response)
        return jsonify({'message': 'Successfully sent message', 'response': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
