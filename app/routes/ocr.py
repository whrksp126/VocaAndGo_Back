from flask import Flask, request, render_template, redirect, url_for
import pytesseract
from PIL import Image
import os

from flask_login import current_user, login_required, login_user

from app.routes import ocr_bp

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

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


def extract_text(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text


### 위치좌표도!!! ###
