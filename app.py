import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

# --- 1. 기본 설정 및 성능 최적화 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 캐시를 사용하여 매번 모델 리스트를 불러오지 않도록 함
@st.cache_resource
def get_model():
    # 가장 빠르고 가벼운 1.5-flash 모델을 기본으로 사용
    return genai.GenerativeModel('gemini-1.5-flash')

# 매뉴얼 데이터를 캐싱하여 파일 읽기 횟수 감소
@st.cache_data
def load_manual_data():
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "현재 등록된 시설개방 지침 데이터가 없습니다."

# 구글 시트 연결 설정 (최초 1회만 실행)
@st.cache_resource
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["google_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# --- 2. 화면 UI ---
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 학교시설개방 스마트 질의응답")
st.markdown("안양과천 교육지원청 시설개방 지침 및 예약 현황을 안내합니다.")

# 사용자 질문 입력
with st.form("qna_form"):
    user_question = st.text_area("궁금한 점을 입력하세요.", height=150, placeholder="예: 체육관 미개방 사유가 뭐야?")
    submitted = st.form_submit_button("질문하기")

    if submitted:
        if not user_question.strip():
            st.warning("질문을 입력해주세요.")
            st.stop()
        
        with st.spinner('지침을 확인 중...'):
            try:
                # 최적화된 데이터 로드
                model = get_model()
                manual_context = load_manual_data()
                sheet = get_gsheet()
                
                # 프롬프트를 간결하게 다듬어 토큰 사용량 절감
                prompt = f"""당신은 안양과천교육지원청 시설개방 AI입니다. 
지침에 근거하여 답변하되, 지침에 없는 내용은 행정실 문의를 안내하세요. 
이용 가능한 시설 문의 시 데이터 내 미예약 학교를 우선 추천하세요.

[지침 데이터]
{manual_context}

[질문]: {user_question}"""

                # 답변 생성
                response = model.generate_content(prompt)
                answer = response.text
                
                # 결과 출력
                st.info(answer)
                
                # 구글 시트 기록
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([now, "익명", user_question, answer])
                st.success("✅ 답변 완료 및 기록되었습니다.")

            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ 일시적으로 사용량이 많습니다. 약 30초 뒤 다시 시도해주세요.")
                else:
                    st.error(f"오류 발생: {e}")
