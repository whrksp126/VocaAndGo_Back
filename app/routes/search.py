from flask import render_template, redirect, url_for, request, session, jsonify
from app.routes import search_bp
from app.models.models import db, Word, Meaning

@search_bp.route('/')
def index():
    # 부분 입력에 따른 단어 검색 기능
    return render_template('index.html')

@search_bp.route('/search_word', methods=['GET'])
def search_word():
    #partial_word = request.args.get('fi')
    partial_word = 'fi'

    if not partial_word:
        return jsonify([])

    search_pattern = f'{partial_word}%'
    print(partial_word)

    results = Word.query.filter(Word.word.like(search_pattern)).all()

    print([word.word for word in results])
    
    return jsonify([word.word for word in results])