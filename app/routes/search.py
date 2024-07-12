import json
from flask import render_template, redirect, url_for, request, session, jsonify
from app.routes import search_bp
from app.models.models import db, Word, Meaning

from flask_login import current_user, login_required, login_user

@login_required
@search_bp.route('/')
def index():
    # 부분 입력에 따른 단어 검색 기능
    return render_template('index.html')


# 사전 검색 API
## 영어(단어) 부분 검색
@login_required
@search_bp.route('/search_word_en', methods=['GET'])
def search_word_en():
    partial_word = request.args.get('word')
    #partial_word = 'fi' # 테스트용

    if not partial_word:
        return jsonify(['잘못된 요청'])

    search_pattern = f'{partial_word}%'

    # 서브 쿼리 : 해당 단어의 id 검색(오름차순 기준 최대 10개까지)
    subquery = (db.session.query(Word.id)
                .filter(Word.word.like(search_pattern))
                .order_by(Word.word.asc())
                .limit(10)
                .subquery())

    # 메인 쿼리 : word, meaning 조인해서 서브 쿼리에 포함된 word id의 데이터만 검색 
    results = (db.session.query(Word, Meaning)
               .outerjoin(Meaning, Word.id == Meaning.word_id)
               .filter(Word.id.in_(subquery))
               .all())
    
    # 단어별로 뜻을 매핑하여 결과 생성
    data = [] # 최종 데이터 담는 리스트
    word_meaning_map = {}
    for word, meaning in results:
        if word.id not in word_meaning_map:
            word_meaning_map[word.id] = {
                #'id': word.id,
                'word': word.word,
                'pronunciation': word.pronunciation,
                'example': json.loads(word.example) if word.example else None, # json 형식으로 파싱
                'meanings': []
            }
        if meaning:
            word_meaning_map[word.id]['meanings'].append(meaning.meaning)

    for word_data in word_meaning_map.values():
        data.append(word_data)

    return jsonify({'code': 200, 'data' : data}), 200


# 사전 검색 API
## 한글(뜻) 부분 검색
@search_bp.route('/search_word_ko', methods=['GET'])
def search_word_ko():
    partial_word = request.args.get('word')
    #partial_word = '구' # 테스트용

    if not partial_word:
        return jsonify(['잘못된 요청'])

    search_pattern = f'{partial_word}%'

    # 서브 쿼리 : 해당 뜻의 word_id 검색(오름차순 기준 최대 10개까지)
    subquery = (db.session.query(Meaning.word_id)
                .filter(Meaning.meaning.like(search_pattern))
                .order_by(Meaning.meaning.asc())
                .limit(10)
                .subquery())
    
    # 메인 쿼리 : word, meaning 조인해서 서브 쿼리에 포함된 word id의 데이터만 검색 
    results = (db.session.query(Word, Meaning)
               .outerjoin(Meaning, Word.id == Meaning.word_id)
               .filter(Word.id.in_(subquery))
               .all())

    # 단어별로 뜻을 매핑하여 결과 생성
    data = [] # 최종 데이터 담는 리스트
    word_meaning_map = {}
    for word, meaning in results:
        if word.id not in word_meaning_map:
            word_meaning_map[word.id] = {
                #'id': word.id,
                'word': word.word,
                'pronunciation': word.pronunciation,
                'example': json.loads(word.example) if word.example else None, # json 형식으로 파싱
                'meanings': [], # word가 가진 모든 뜻
                'main_keyword': [] # partial_word에 포함된 뜻만
            }

        if meaning:
            # meaning 전부 추가
            word_meaning_map[word.id]['meanings'].append(meaning.meaning)

            # partial_word에 포함된 meaning만 추가
            keyword = meaning.meaning
            if keyword.startswith(partial_word): # 'partial_word'로 시작하는지 확인
                word_meaning_map[word.id]['main_keyword'].append(keyword)

    for word_data in word_meaning_map.values():
        data.append(word_data)

    return jsonify({'code': 200, 'data' : data}), 200