from flask import render_template, redirect, url_for, request, session, jsonify, send_file, send_from_directory
from app import db
from app.routes import fcm_bp
from app.models.models import db, User, UserHasToken
from config import FCM_API_KEY

from flask_login import current_user, login_required, login_user, logout_user

import json
from gtts import gTTS
import os
import uuid
import io

import firebase_admin
from firebase_admin import credentials, messaging
from pyfcm import FCMNotification


@fcm_bp.route('/fcm_html')
def fcm_html():
    return render_template('fcm3.html')


@fcm_bp.route('/firebase-messaging-sw.js')
def firebase_messaging_sw():
    return send_from_directory('static', 'firebase-messaging-sw.js')


@fcm_bp.route('/send_notification_test', methods=['POST'])
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
@fcm_bp.route('/get_token', methods=['POST'])
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




########################

# 토큰 저장 API
@fcm_bp.route('/save_token', methods=['POST'])
def save_token():
    token = request.json.get('token')
    print("@#$@#$curr", current_user.id)

    if not token:
        return jsonify({'code': 400, 'msg': "토큰이 없습니다"})

    token_item = db.session.query(UserHasToken)\
                    .filter(UserHasToken.user_id == current_user.id)\
                    .filter(UserHasToken.token == token)\
                    .all()

    if token_item is None:
        item  = UserHasToken(
            user_id = current_user.id,
            token = token,
        )

        db.session.add(item)
        db.session.commit()



# FCM API 키 (Firebase Console에서 확인 가능)
push_service = FCMNotification(service_account_file='app/config/vocaandgo-firebase-adminsdk-xyi9u-e4f0ccc423.json',
                                 project_id='vocaandgo')


# FCM 메시지 전송 함수
def send_push_notification(title, message, token):
    result = push_service.notify(fcm_token=token, 
                                notification_title=title, 
                                notification_body=message, 
                                notification_image=None
                            )

    return result

# 메시지 전송 API
@fcm_bp.route('/send-notification', methods=['GET'])
def send_notification():
    # title = request.json.get('title')
    # message = request.json.get('message')
    title = 'test_title'
    message = 'test_message'

    try:
        # # DB에서 저장된 토큰 조회
        # cursor.execute("SELECT token FROM fcm_tokens")
        # tokens = cursor.fetchall()

        tokens = db.session.query(UserHasToken).all()

        # 모든 토큰에 푸시 알림 전송
        results = []
        for token in tokens:
            result = send_push_notification(title, message, token.token)
            results.append(result)

        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
