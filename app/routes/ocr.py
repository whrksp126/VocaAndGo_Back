from flask import Flask, request, render_template, redirect, url_for
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import os

from flask_login import current_user, login_required, login_user

from app.routes import ocr_bp

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'app/static/uploads/'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@ocr_bp.route('/ocr')
def index():
    return render_template('ocr_test.html')


@ocr_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        text = extract_text(filepath)
        return render_template('ocr_test.html', extracted_text=text)


def preprocess_image(image_path):
    img = Image.open(image_path)
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)  # 해상도 높이기
    img = img.convert('L')  # 회색조로 변환
    img = img.filter(ImageFilter.SHARPEN)  # 선명하게 하기
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)  # 대비 강화
    img = img.point(lambda x: 0 if x < 160 else 255, '1')  # 이진화 처리
    return img

def extract_text(image_path):
    img = preprocess_image(image_path)
    custom_config = r'--oem 3 --psm 6'  # PSM 모드를 6으로 설정
    data = pytesseract.image_to_data(img, config=custom_config, lang='kor+eng', output_type=pytesseract.Output.DATAFRAME)
    extracted_text = data.to_dict(orient='records')
    return extracted_text


'''
사진 업로드하지 말고 스트림? 으로 확인할 수 있게 하자!!
'''