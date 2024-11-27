celery_worker_beat.py 스크립트를 Systemd로 관리하려면 각각의 Worker와 Beat 프로세스를 별도로 관리하도록 서비스 파일을 작성해야 합니다. 아래는 구체적인 설정 방법입니다.

1. Celery Worker Systemd 서비스 파일
Celery Worker를 실행하는 서비스 파일을 작성합니다.

서비스 파일 생성
/etc/systemd/system/voca-fcm-celery-worker.service 파일 생성:

ini
코드 복사

[Unit]
Description=Celery Worker Service
After=network.target

[Service]
User=order# Celery를 실행할 사용자
Group=order
WorkingDirectory=/var/www/vocaandgo # 프로젝트 루트 경로
ExecStart=/var/www/vocaandgo/.venv/bin/python3 /var/www/vocaandgo/app/celery_worker_beat.py worker
Restart=always
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target

2. Celery Beat Systemd 서비스 파일
Celery Beat를 실행하는 서비스 파일을 작성합니다.

서비스 파일 생성
/etc/systemd/system/voca-fcm-celery-beat.service 파일 생성:

ini
코드 복사
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
User=order  # Celery를 실행할 사용자
Group=order
WorkingDirectory=/var/www/vocaandgo  # 프로젝트 루트 경로
ExecStart=/var/www/vocaandgo/.venv/bin/python3 /var/www/vocaandgo/app/celery_worker_beat.py beat
Restart=always
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target

3. Systemd 서비스 활성화
서비스 파일을 작성한 후 Systemd에 반영하고 활성화합니다.

명령어 실행
bash
코드 복사
# 데몬 리로드
sudo systemctl daemon-reload

# Celery Worker 서비스 활성화 및 시작
sudo systemctl enable voca-fcm-celery-worker.service
sudo systemctl start voca-fcm-celery-worker.service

# Celery Beat 서비스 활성화 및 시작
sudo systemctl enable voca-fcm-celery-beat.service
sudo systemctl start voca-fcm-celery-beat.service
4. 로그 확인
Celery Worker와 Beat의 상태를 확인하고 로그를 모니터링합니다.

서비스 상태 확인
bash
코드 복사
sudo systemctl status voca-fcm-celery-worker.service
sudo systemctl status voca-fcm-celery-beat.service
로그 확인
bash
코드 복사
# Worker 로그
sudo journalctl -u voca-fcm-celery-worker.service

# Beat 로그
sudo journalctl -u voca-fcm-celery-beat.service
5. 구체적인 설정 요소
User와 Group: Celery를 실행할 사용자와 그룹을 설정합니다. your-username과 your-groupname을 실제 사용자 정보로 대체하세요.
WorkingDirectory: Celery 애플리케이션이 실행되는 프로젝트 경로를 설정합니다.
Restart=always: Celery 프로세스가 종료되더라도 자동으로 재시작되도록 설정합니다.
Environment: 필요한 환경 변수를 추가할 수 있습니다.
6. 추가 권장 사항
Redis 활성화 확인: Celery가 Redis를 사용하는 경우, Redis 서비스가 활성화되어 있는지 확인합니다.
bash
코드 복사
sudo systemctl status redis
Celery 로그 관리: /path/to/your/app/celery.log에 로그가 저장되도록 설정되어 있으니 로그 파일이 제대로 쓰이는지 확인하고, 로그 파일이 커지면 로테이션을 설정합니다.
이제 Celery Worker와 Beat 프로세스가 Systemd를 통해 관리되며, 서버 재부팅 시에도 자동으로 실행됩니다.

