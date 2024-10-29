import json
import re
from flask import render_template, redirect, url_for, request, session, jsonify
from sqlalchemy import text
from sqlalchemy.orm import joinedload
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

    # 서브 쿼리 : 해당 단어의 id 검색(오름차순 기준 최대 10개까지)
    subquery = (db.session.query(Voca.id)
                .filter(Voca.word.like(f"%{word}%"))
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
    data = [] # 최종 데이터 담는 리스트
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

    return jsonify({'code': 200, 'data' : data}), 200


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

    # 메인 쿼리 : word, meaning, example 조인해서 서브 쿼리에 포함된 word id의 데이터만 검색 
    results = (db.session.query(Voca, VocaMeaning, VocaExample)
               .outerjoin(VocaMeaningMap, Voca.id == VocaMeaningMap.voca_id)
               .outerjoin(VocaMeaning, VocaMeaningMap.meaning_id == VocaMeaning.id)
               .outerjoin(VocaExampleMap, Voca.id == VocaExampleMap.voca_id)
               .outerjoin(VocaExample, VocaExampleMap.example_id == VocaExample.id)
               .filter(Voca.id.in_(subquery))
               .all())
    
    # 단어별로 뜻과 예문을 매핑하여 결과 생성
    data = [] # 최종 데이터 담는 리스트
    word_meaning_map = {}
    for word, meaning, example in results:
        # 단어 및 뜻 데이터 처리
        if word.id not in word_meaning_map:
            word_meaning_map[word.id] = {
                'word': word.word,
                'pronunciation': word.pronunciation,
                'examples': [],
                'meanings': []
            }
        
        # 뜻 추가
        if meaning:
            word_meaning_map[word.id]['meanings'].append(meaning.meaning)
        
        # 예문 추가
        if example:
            word_meaning_map[word.id]['examples'].append({"id": example.id, "exam_en": example.exam_en, "exam_ko": example.exam_ko})

    for word_data in word_meaning_map.values():
        data.append(word_data)

    return jsonify({'code': 200, 'data' : data}), 200


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

    # 서점만 가져오는 쿼리 (temp)
    bookstore_query = (db.session.query(Bookstore).all())

    # 단어별로 뜻을 매핑하여 결과 생성
    data = [] # 최종 데이터 담는 리스트
    bookstore_map = {}
    for bs in bookstore_query:
        bookstore_map[bs.id] = {
            'name': bs.name,
            'downloads': bs.downloads,
            'category': bs.category,
            'color': bs.color,
            'book_id': bs.book_id,
        }

    for bookstore_data in bookstore_map.values():
        data.append(bookstore_data)

    return jsonify({'code': 200, 'data' : data}), 200

    '''
    # 서점 쿼리 : 서점 데이터 검색 (ALL)
    bookstore_query = (db.session.query(Bookstore)
                .join(VocaBookMap, Bookstore.book_id == VocaBookMap.book_id).all()
                )
    # 여기서부터 다시 만들어 가야해,,,
    # 서점 쿼리 : 서점 데이터 검색 (ALL)
    bookstore_query = (db.session.query(Bookstore)
                .join(VocaBookMap, Bookstore.book_id == VocaBookMap.book_id).all()
                )
    '''

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


# # 서점 데이터 더미
# vocabulary_store_dummy_data = [
#   {
#     "id" : 1,
#     "name" : "토익 준비용 🔥",
#     "downloads" : 157025,
#     "category" : "HOT",
#     "color" : {
#       "main" : "#FF8DD4",
#       "sub" : "#FFD2EF",
#       "background" : "#FFEFFA",
#     },
#     "hide": "N",
#     "words" : [
#       {
#         "id" : 1,
#         "word" : "be",
#         "pronunciation": "bi; (강) biː",
#         "meaning": ["…이다", "있다", "존재하다"],
#         "examples": [
#           {"origin" : "I think, therefore I am.", "meaning" : "나는 생각한다, 그러므로 나는 존재한다"},
#           {"origin" : "Kennedy is no more.", "meaning" : "케네디는 가고 없다"},
#         ],
#         "description" : ""
#       },
#       {
#         id : 2,
#         word : "tuesday",
#         meaning: ["화요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 3,
#         word : "wednesday",
#         meaning: ["수요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 4,
#         word : "thursday",
#         meaning: ["목요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 5,
#         word : "friday",
#         meaning: ["금요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 6,
#         word : "saturday",
#         meaning: ["토요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 7,
#         word : "sunday",
#         meaning: ["일요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#     ]
#   },
#   {
#     id : 2,
#     name : "고등 수능 영단어 👀",
#     downloads : 3671,
#     category : null,
#     color : {
#       main : "#CD8DFF",
#       sub : "#EAD2FF",
#       background : "#F6EFFF",
#     },
#     words : [
#       {
#         id : 1,
#         word : "monday",
#         meaning: ["월요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 2,
#         word : "tuesday",
#         meaning: ["화요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 3,
#         word : "wednesday",
#         meaning: ["수요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 4,
#         word : "thursday",
#         meaning: ["목요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 5,
#         word : "friday",
#         meaning: ["금요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 6,
#         word : "saturday",
#         meaning: ["토요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 7,
#         word : "sunday",
#         meaning: ["일요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#     ]
#   },
#   {
#     id : 3,
#     name : "30일 완성 TEPS 👍",
#     downloads : 9307,
#     category : null,
#     color : {
#       main : "#74D5FF",
#       sub : "#C6ECFF",
#       background : "#EAF6FF",
#     },
#     words : [
#       {
#         id : 1,
#         word : "monday",
#         meaning: ["월요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 2,
#         word : "tuesday",
#         meaning: ["화요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 3,
#         word : "wednesday",
#         meaning: ["수요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 4,
#         word : "thursday",
#         meaning: ["목요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 5,
#         word : "friday",
#         meaning: ["금요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 6,
#         word : "saturday",
#         meaning: ["토요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 7,
#         word : "sunday",
#         meaning: ["일요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#     ]
#   },
#   {
#     id : 4,
#     name : "기적의 말하기 영단어 🗣️",
#     downloads : 970,
#     category : "NEW",
#     color : {
#       main : "#42F98B",
#       sub : "#B2FDCC",
#       background : "#E2FFE8",
#     },
#     words : [
#       {
#         id : 1,
#         word : "monday",
#         meaning: ["월요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 2,
#         word : "tuesday",
#         meaning: ["화요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 3,
#         word : "wednesday",
#         meaning: ["수요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 4,
#         word : "thursday",
#         meaning: ["목요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 5,
#         word : "friday",
#         meaning: ["금요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 6,
#         word : "saturday",
#         meaning: ["토요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 7,
#         word : "sunday",
#         meaning: ["일요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#     ]
#   },
#   {
#     id : 5,
#     name : "챗GPT 영어 공부 - 영단어편 💭",
#     downloads : 235480,
#     category : "HOT",
#     color : {
#       main : "#FFBD3C",
#       sub : "#FFE5AE",
#       background : "#FFF6DF",
#     },
#     words : [
#       {
#         id : 1,
#         word : "monday",
#         meaning: ["월요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 2,
#         word : "tuesday",
#         meaning: ["화요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 3,
#         word : "wednesday",
#         meaning: ["수요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 4,
#         word : "thursday",
#         meaning: ["목요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 5,
#         word : "friday",
#         meaning: ["금요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 6,
#         word : "saturday",
#         meaning: ["토요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#       {
#         id : 7,
#         word : "sunday",
#         meaning: ["일요일"],
#         example: [
#           {origin : "", meaning : ""}
#         ],
#         description : ""
#       },
#     ]
#   },
# ]
