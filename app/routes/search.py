import json
import re
from flask import render_template, redirect, url_for, request, session, jsonify
from sqlalchemy import text
from app.routes import search_bp
from app.models.models import db, Word, Meaning

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
    subquery = (db.session.query(Word.id)
                .filter(Word.word.like(word))
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
        example = json.loads(word.example) if word.example else None
        if isinstance(example, list):
            example = [{"origin": item["exam_en"], "meaning": item["exam_ko"]} for item in example]
        else:
            example = None 

        if word.id not in word_meaning_map:
            word_meaning_map[word.id] = {
                #'id': word.id,
                'word': word.word,
                'pronunciation': word.pronunciation,
                'example': example,
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
        example = json.loads(word.example) if word.example else None
        if isinstance(example, list):
            example = [{"origin": item["exam_en"], "meaning": item["exam_ko"]} for item in example]
        else:
            example = None 
        if word.id not in word_meaning_map:
            word_meaning_map[word.id] = {
                #'id': word.id,
                'word': word.word,
                'pronunciation': word.pronunciation,
                'example': example,
                'meanings': []
            }
        if meaning:
            word_meaning_map[word.id]['meanings'].append(meaning.meaning)

    for word_data in word_meaning_map.values():
        data.append(word_data)

    return jsonify({'code': 200, 'data' : data}), 200


## 한글(뜻) 부분 검색
# 1. 초성만 검색('ㄱ')  2. 글자+초성 검색('구ㄱ')  3. 글자 검색('구급차')
@search_bp.route('/partial/ko', methods=['GET'])
def search_word_korean():
    partial_word = request.args.get('word')
    word_split = [] # 한 글자씩 담기
    for w in range(len(partial_word)):
        word_split.append(partial_word[w])

    if not partial_word:
        return jsonify({'code': 400, 'message': '잘못된 요청입니다.'}), 400

    first_char = word_split[0]
    last_char = word_split[-1]

    if identify_character(first_char) == '초성':
        # 전체 초성인 경우
        regex_pattern = '^'
        for w in word_split:
            unicode_range = get_unicode_range_for_initial(w)
            regex_pattern += unicode_range
    elif identify_character(first_char) == '한글' and identify_character(last_char) == '초성':
        # 마지막 글자만 초성일 경우
        regex_pattern = '^' + ''.join(map(re.escape, partial_word[:-1]))
        unicode_range = get_unicode_range_for_initial(last_char)
        regex_pattern += unicode_range
    elif identify_character(first_char) == '한글' and identify_character(last_char) == '한글':
        # 한글인 경우
        regex_pattern = re.escape(partial_word) + '.*'
    else:
        return jsonify({'code': 400, 'message': '잘못된 요청입니다.'}), 400
    
    #print('정규표현식 패턴:', regex_pattern)

    # SQL 쿼리 작성
    query = text(f"""
        SELECT * 
        FROM meaning 
        WHERE REPLACE(meaning, ' ', '') REGEXP :pattern 
        ORDER BY meaning ASC 
        LIMIT 10
    """)

    # 쿼리 실행
    results = db.session.execute(query, {'pattern': regex_pattern}).fetchall()

    # 결과를 JSON 형태로 반환 (word + meaning)
    result_list = []
    for result in results:
        word = db.session.query(Word).filter_by(id=result.word_id).first()
        example = json.loads(word.example) if word.example else None
        if isinstance(example, list):
            example = [{"origin": item["exam_en"], "meaning": item["exam_ko"]} for item in example]
        else:
            example = None 
        result_data = {
            'word': word.word,
            'pronunciation': word.pronunciation,
            'example': example,
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




# # 서점 데이터 더미
# vocabulary_store_dummy_data = [
#   {
#     id : 1,
#     name : "토익 준비용 🔥",
#     downloads : 157025,
#     category : "HOT",
#     color : {
#       main : "#FF8DD4",
#       sub : "#FFD2EF",
#       background : "#FFEFFA",
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
