import json
import re
from flask import render_template, redirect, url_for, request, session, jsonify
from sqlalchemy import text, select
from sqlalchemy.orm import joinedload, contains_eager
from app.routes import search_bp
from app.models.models import db, VocaBook, Voca, VocaMeaning, VocaExample, VocaBookMap, VocaMeaningMap, VocaExampleMap, Bookstore

from flask_login import current_user, login_required, login_user

# @login_required
@search_bp.route('/')
def index():
    # 부분 입력에 따른 단어 검색 기능
    return render_template('index.html')

################
# 사전 검색 API #
################
## 영어(단어) 전체 검색
# @login_required
@search_bp.route('/en', methods=['GET'])
def search_voca_word_en():

    word = request.args.get('word')
    print('word : ', word)

    if not word:
        return jsonify(['잘못된 요청'])

    # 서브 쿼리 : 해당 단어와 완전히 일치하는 id 검색 (오름차순 기준 최대 10개까지)
    subquery = (db.session.query(Voca.id)
                .filter(Voca.word == word)  # 완전 일치 검색
                .order_by(Voca.word.asc())
                .limit(10)
                .subquery())

    # 메인 쿼리 : word, meaning 조인해서 서브 쿼리에 포함된 word id의 데이터만 검색
    results = (db.session.query(Voca, VocaMeaning)
               .outerjoin(VocaMeaningMap, Voca.id == VocaMeaningMap.voca_id)
               .outerjoin(VocaMeaning, VocaMeaningMap.meaning_id == VocaMeaning.id)
               .filter(Voca.id.in_(subquery))
               .all())
    
    # 단어별로 뜻을 매핑하여 결과 생성
    data = []  # 최종 데이터 담는 리스트
    word_meaning_map = {}
    for word, meaning in results:
        # 예문 데이터 처리
        example_data = []
        for example_map in db.session.query(VocaExampleMap).filter_by(voca_id=word.id).all():
            example = db.session.query(VocaExample).filter_by(id=example_map.example_id).first()
            if example:
                example_data.append({"id": example.id, "exam_en": example.exam_en, "exam_ko": example.exam_ko})

        # 단어 및 뜻 데이터 처리
        if word.id not in word_meaning_map:
            word_meaning_map[word.id] = {
                'word': word.word,
                'pronunciation': word.pronunciation,
                'examples': example_data,
                'meanings': []
            }

        if meaning:
            word_meaning_map[word.id]['meanings'].append(meaning.meaning)

    for word_data in word_meaning_map.values():
        data.append(word_data)

    return jsonify({'code': 200, 'data': data}), 200

## 영어(단어) 부분 검색
# @login_required
@search_bp.route('/partial/en', methods=['GET'])
def search_word_en():

    partial_word = request.args.get('word')

    if not partial_word:
        return jsonify(['잘못된 요청'])

    search_pattern = f'{partial_word}%'

    # 서브 쿼리 : 해당 단어의 id 검색(오름차순 기준 최대 10개까지)
    subquery = (db.session.query(Voca.id)
                .filter(Voca.word.like(search_pattern))
                .order_by(Voca.word.asc())
                .limit(10)
                .subquery())

    # 단어와 발음 가져오기
    words = db.session.query(Voca).filter(Voca.id.in_(subquery)).all()

    # 뜻 가져오기
    meanings = (db.session.query(VocaMeaningMap.voca_id, VocaMeaning.meaning)
                .join(VocaMeaning, VocaMeaningMap.meaning_id == VocaMeaning.id)
                .filter(VocaMeaningMap.voca_id.in_(subquery))
                .all())

    # 예문 가져오기
    examples = (db.session.query(VocaExampleMap.voca_id, VocaExample.id, VocaExample.exam_en, VocaExample.exam_ko)
                .join(VocaExample, VocaExampleMap.example_id == VocaExample.id)
                .filter(VocaExampleMap.voca_id.in_(subquery))
                .all())

    # 단어별로 뜻과 예문을 매핑하여 결과 생성
    data = []  # 최종 데이터 담는 리스트
    word_map = {word.id: {
        'word': word.word,
        'pronunciation': word.pronunciation,
        'meanings': [],
        'examples': []
    } for word in words}

    # 뜻 추가
    for voca_id, meaning in meanings:
        if meaning not in word_map[voca_id]['meanings']:
            word_map[voca_id]['meanings'].append(meaning)

    # 예문 추가
    for voca_id, example_id, exam_en, exam_ko in examples:
        example_data = {"id": example_id, "exam_en": exam_en, "exam_ko": exam_ko}
        if example_data not in word_map[voca_id]['examples']:
            word_map[voca_id]['examples'].append(example_data)

    # 최종 데이터 리스트 생성
    data = list(word_map.values())

    return jsonify({'code': 200, 'data': data}), 200


## 한글(뜻) 부분 검색
# 1. 초성만 검색('ㄱ')  2. 글자+초성 검색('구ㄱ')  3. 글자 검색('구급차')
@search_bp.route('/partial/ko', methods=['GET'])
def search_word_korean():
    partial_word = request.args.get('word')
    word_split = list(partial_word) if partial_word else [] # 한 글자씩 담기

    if not partial_word:
        return jsonify({'code': 400, 'message': '잘못된 요청입니다.'}), 400

    first_char = word_split[0]
    last_char = word_split[-1]

    if identify_character(first_char) == '초성':
        # 전체 초성인 경우
        regex_pattern = '^' + ''.join(get_unicode_range_for_initial(w) for w in word_split)
    elif identify_character(first_char) == '한글' and identify_character(last_char) == '초성':
        # 마지막 글자만 초성일 경우
        regex_pattern = '^' + re.escape(''.join(partial_word[:-1])) + get_unicode_range_for_initial(last_char)
    elif identify_character(first_char) == '한글' and identify_character(last_char) == '한글':
        # 한글인 경우
        regex_pattern = re.escape(partial_word) + '.*'
    else:
        return jsonify({'code': 400, 'message': '잘못된 요청입니다.'}), 400
    
    # SQL 쿼리 작성
    query = text(f"""
        SELECT voca_meaning.id, voca_meaning.meaning, voca_meaning_map.voca_id
        FROM voca_meaning
        JOIN voca_meaning_map ON voca_meaning.id = voca_meaning_map.meaning_id
        WHERE REPLACE(voca_meaning.meaning, ' ', '') REGEXP :pattern
        ORDER BY voca_meaning.meaning ASC
        LIMIT 10
    """)

    # 쿼리 실행
    results = db.session.execute(query, {'pattern': regex_pattern}).fetchall()

    # 결과를 JSON 형태로 반환 (word + meaning + example)
    result_list = []
    voca_ids = [result.voca_id for result in results]
    voca_records = db.session.query(Voca).filter(Voca.id.in_(voca_ids)).all()
    voca_dict = {voca.id: voca for voca in voca_records}

    for result in results:
        voca = voca_dict.get(result.voca_id)
        
        if not voca:
            continue

        # 예문 데이터 처리
        example_data = []
        example_maps = db.session.query(VocaExampleMap).filter_by(voca_id=voca.id).all()
        example_ids = [example_map.example_id for example_map in example_maps]
        examples = db.session.query(VocaExample).filter(VocaExample.id.in_(example_ids)).all()
        
        for example in examples:
            example_data.append({"id": example.id, "exam_en": example.exam_en, "exam_ko": example.exam_ko})

        result_data = {
            'word': voca.word,
            'pronunciation': voca.pronunciation,
            'examples': example_data,
            'meaning': result.meaning,
        }
        result_list.append(result_data)

    return jsonify({'code': 200, 'data': result_list}), 200


# 한글 자음 리스트
#CHO = [chr(i) for i in range(0x1100, 0x1113)]  # 초성
CHO = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ',
        'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

# 초성인지 확인하는 함수
# 맞으면 True, 아니면 False 반환
def is_initial(char):
    return char in CHO

# 글자인지 확인하는 함수
# 맞으면 True, 아니면 False 반환
def is_hangul(char):
    return '가' <= char <= '힣'

def identify_character(char):
    if is_initial(char):
        return '초성'
    elif is_hangul(char):
        return '한글'
    else:
        return '기타'

# 초성에 해당하는 유니코드 범위 반환 함수
def get_unicode_range_for_initial(char):
    initial_index = CHO.index(char)
    start = chr(0xAC00 + initial_index * 21 * 28) # 가
    end = chr(0xAC00 + (initial_index + 1) * 21 * 28 - 1) # 깋
    return f'[{start}-{end}]' # [가-깋]


##############
## 서점 검색 ##
##############

## 서점 데이터 API
# bookstore, voca, voca_meaning, voca_example 테이블의 모든 데이터를 가져옴
# @login_required
@search_bp.route('/bookstore', methods=['GET'])
def search_bookstore_all():
    query = text("""
        SELECT 
            bs.id AS bookstore_id, bs.name AS bookstore_name, bs.downloads, bs.category, bs.hide,
            vb.id AS voca_book_id,
            v.id AS voca_id, v.word, v.pronunciation,
            vm.meaning AS meaning,
            ve.exam_en AS example_en, ve.exam_ko AS example_ko
        FROM bookstore bs
        LEFT JOIN voca_book vb ON bs.book_id = vb.id
        LEFT JOIN voca_book_map vbm ON vb.id = vbm.book_id
        LEFT JOIN voca v ON vbm.voca_id = v.id
        LEFT JOIN voca_meaning_map vmm ON v.id = vmm.voca_id
        LEFT JOIN voca_meaning vm ON vmm.meaning_id = vm.id
        LEFT JOIN voca_example_map vem ON v.id = vem.voca_id
        LEFT JOIN voca_example ve ON vem.example_id = ve.id
    """)

    rows = db.session.execute(query).fetchall()

    # 데이터 구조화
    results = {}
    for row in rows:
        bookstore_id = row.bookstore_id
        voca_id = row.voca_id

        # 서점 정보 구성
        if bookstore_id not in results:
            results[bookstore_id] = {
                "id": bookstore_id,
                "name": row.bookstore_name,
                "downloads": row.downloads,
                "category": row.category,
                "hide": row.hide,
                "words": {}
            }

        # 단어 정보 구성
        if voca_id not in results[bookstore_id]["words"]:
            results[bookstore_id]["words"][voca_id] = {
                "id": voca_id,
                "word": row.word,
                "pronunciation": row.pronunciation,
                "meaning": [],
                "examples": []
            }

        # 단어 뜻 추가
        if row.meaning and row.meaning not in results[bookstore_id]["words"][voca_id]["meaning"]:
            results[bookstore_id]["words"][voca_id]["meaning"].append(row.meaning)

        # 단어 예문 추가
        if row.example_en and row.example_ko:
            results[bookstore_id]["words"][voca_id]["examples"].append({
                "origin": row.example_en,
                "meaning": row.example_ko
            })

    # 결과를 리스트로 변환
    final_results = list(results.values())
    
    return jsonify({'code': 200, 'data' : final_results}), 200

    '''
    # bookstore 테이블의 모든 데이터를 가져옴
    bookstores = db.session.query(Bookstore) \
        .options(
            joinedload(Bookstore.voca_book)  # VocaBook과의 관계 로드
                .joinedload(VocaBook.voca_books)  # VocaBookMap 로드
                .joinedload(VocaBookMap.voca),  # Voca 로드
            joinedload(Bookstore.voca_book)
                .joinedload(VocaBook.voca_books)
                .joinedload(VocaBookMap.voca)
                .joinedload(Voca.voca_meanings),  # VocaMeaning 로드
            joinedload(Bookstore.voca_book)
                .joinedload(VocaBook.voca_books)
                .joinedload(VocaBookMap.voca)
                .joinedload(Voca.voca_examples)  # VocaExample 로드
        ).all()

    if not bookstores:
        return jsonify({'code': 404, 'message': 'No bookstores found'}), 404

    results = []

    for bookstore in bookstores:
        voca_book = bookstore.voca_book
        
        if voca_book:
            words = []
            # VocaBookMap을 통해 Voca 데이터를 가져옴
            for voca_map in voca_book.voca_books:
                voca = voca_map.voca
                
                # 단어 뜻 가져오기
                meanings = [meaning_map.meaning.meaning for meaning_map in voca.voca_meanings]
                
                # 단어 예문 가져오기
                examples = [{"origin": example_map.example.exam_en, "meaning": example_map.example.exam_ko}
                            for example_map in voca.voca_examples]
                
                # 단어 정보 구성
                words.append({
                    "id": voca.id,
                    "word": voca.word,
                    "pronunciation": voca.pronunciation,
                    "meaning": meanings,
                    "examples": examples,
                    "description": ""
                })

            # 서점 정보 구성
            results.append({
                "id": bookstore.id,
                "name": bookstore.name,
                "downloads": bookstore.downloads,
                "category": bookstore.category,
                "color": json.loads(bookstore.color),
                "hide": bookstore.hide,
                "words": words
            })
    '''

    return jsonify({'code': 200, 'data': 'ㅅ'}), 200

