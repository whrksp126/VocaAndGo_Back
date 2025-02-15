import traceback
from app.routes import check_bp
from flask import render_template, jsonify
from app.models.models import db, VocaBook, VocaBookMap, VocaMeaningMap, VocaExampleMap, Bookstore, Voca
import enchant
from nltk.corpus import words
import nltk
import pandas as pd
import json
import math
from io import BytesIO
import spacy
import pyinflect
import pandas as pd

# NLTK 단어 사전 다운로드 (최초 한 번 필요)
#nltk.download('words')

# NLTK 단어 목록을 집합으로 저장 (빠른 조회를 위해)
#nltk_words_set = set(words.words())

# 영어 사전 객체 생성 -> 영단어인데 인식 못 하는 데이터가 많아 일단 보류
#english_dict = enchant.Dict("en_US")

@check_bp.route('/')
def temp():
    return render_template('check_test.html')

# 영단어 동사형 추가(품사가 동사일 경우만)
@check_bp.route('/tense_verb')
def get_tense_verb():
    # DB word 데이터 가져오기
    words_data = db.session.query(Voca.id, Voca.word).all()

    # 영어 모델 로드
    nlp = spacy.load("en_core_web_sm")

    # 특정 단어에 대한 다양한 동사형 반환 함수
    def get_verb_forms(words_data):
        # 결과를 저장할 리스트
        verb_forms_list = []

        for id, word in words_data:
            try:
                # 텍스트 처리
                doc = nlp(word)
                token = doc[0]
                print(f"단어: {token.text}, 품사: {token.pos_}, 어간: {token.lemma_}")
                
                if token.pos_ == "VERB":
                    # 각 단어에 대한 딕셔너리를 새로 생성
                    verb_forms = {}

                    # 다양한 형태의 동사형 추가
                    base_form = token.lemma_  # 기본형
                    past_form = token._.inflect("VBD")  # 과거형
                    gerund_form = token._.inflect("VBG")  # 현재 분사형 (동명사)
                    third_person_singular = token._.inflect("VBZ")  # 3인칭 단수 현재형
                    past_participle = token._.inflect("VBN")  # 과거 분사형
                    infinitive = token._.inflect("VB")  # 동사 원형(부정사)
                    imperative = token._.inflect("VB")  # 명령형 (부정사와 동일)

                    # 각 변형을 딕셔너리에 저장
                    verb_forms['id'] = id
                    verb_forms['base_form'] = base_form
                    verb_forms['past_form'] = past_form
                    verb_forms['gerund_form'] = gerund_form
                    verb_forms['third_person_singular'] = third_person_singular
                    verb_forms['past_participle'] = past_participle
                    verb_forms['infinitive'] = infinitive
                    verb_forms['imperative'] = imperative

                    # 생성된 딕셔너리를 리스트에 추가
                    verb_forms_list.append(verb_forms)
                    
            except Exception as e:
                print(f"❌ 오류 발생: {word} 처리 중 오류 발생!\n{traceback.format_exc()}")  # 오류 출력
                verb_forms_list.append({"id": id, "word": word, "error": str(e)})  # 오류 정보 기록

        return verb_forms_list

    # 동사형 가져오기
    verb_forms = get_verb_forms(words_data)
    print(f"✅ 총 {len(verb_forms)}개의 단어 처리 완료!")

    # 결과를 데이터프레임으로 변환
    df = pd.DataFrame(verb_forms)

    # 엑셀로 저장
    df.to_excel("heyvoca_verb.xlsx", index=False)
    print("✅ 엑셀 파일 저장 완료: heyvoca_verb.xlsx")

    return jsonify({'code': 200, 'data': 'success'}), 200

# 영단어 시제 업데이트(동사일 경우)
@check_bp.route('/voca_update')
def update_verb_forms():
    try:
        ### 동사 시제 데이터 전처리
        ## 1. 파일 불러오기
        df = pd.read_excel('C:/Users/gih12/workspaces/hey_voca/spacy/heyvoca_verb_v2.xlsx', index_col=0)
        
        ## 2. dict 형태로 변환
        dict_data = df.to_dict(orient="records")  # 리스트[딕셔너리] 형태

        ## 3. id 값만 추출해서 리스트 생성
        voca_ids = [item["voca_id"] for item in dict_data]  # ⚠ json_data가 아니라 dict_data 사용

        ## 4. DB에서 해당 ID를 가진 레코드 가져오기
        voca_records = db.session.query(Voca).filter(Voca.id.in_(voca_ids)).all()

        ## 5. 각 레코드의 id에 맞는 verb_forms 업데이트
        for voca in voca_records:
            print(voca.id)
            matching_data = next((item for item in dict_data if item["voca_id"] == voca.id), None)  # ⚠ json_data가 아니라 dict_data 사용
            
            if matching_data:
                #print(json.dumps(matching_data, ensure_ascii=False))
                # JSON 문자열로 변환 후 DB에 저장
                voca.verb_forms = json.dumps(matching_data, ensure_ascii=False)  # 쌍따옴표 JSON 저장
                
            else:
                print(f"No matching data found for id {voca.id}")

        # 변경 사항 커밋
        db.session.commit()

        return jsonify({'code': 200, 'data': 'Voca table updated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()  # 예외 발생 시 롤백
        return jsonify({"code": 500, "error": str(e)}), 500
