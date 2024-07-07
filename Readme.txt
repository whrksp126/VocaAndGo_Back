https://vocaandgo.ghmate.com/


-----------------orderandgo debugging-----------------
[가상환경 실행]
cd /home/order/orderandgo/. .venv/bin/activate
[systemctl stop]
sudo systemctl stop vocaandgo

[플라스크 수동 실행]
/home/order/orderandgo/.venv/bin/gunicorn --config /home/order/orderandgo/gunicorn.config.socket.py

/var/www/vocaandgo/.venv/bin/gunicorn --config /var/www/vocaandgo/gunicorn.config.socket.py

[에러, 프린트 로그 모니터링]
tail -f /home/order/orderandgo/gunicorn_log/errorlog.txt

tail -f /var/www/vocaandgo/gunicorn_log/errorlog.txt

[기존 서버 재실행]: 디버깅 종료 후 서버 정상 작동 하고 종료!
sudo systemctl restart vocaandgo
-----------------orderandgo debugging-----------------


gh_home
cd /var/www/vocaandgo
flask 설치 완료 systemd 설정해서 항동 동작하고 있음


### tesseract ocr 설정 ###
https://github.com/UB-Mannheim/tesseract/wiki
에서 exe파일을 설치하고, 
설치 경로를 config.py 파일 pytesseract.pytesseract.tesseract_cmd 변수에 작성한다.

