import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

# --- 1. API 및 성능 최적화 설정 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_resource
def get_model():
    """사용 가능한 모델 중 최적의 모델명을 찾아 연결합니다."""
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 1.5-flash가 있으면 우선 선택, 없으면 첫 번째 가능한 모델 선택
    target = next((m for m in available_models if "1.5-flash" in m), available_models[0])
    return genai.GenerativeModel(target)

@st.cache_data
def load_manual_data():
    """매뉴얼 텍스트를 메모리에 저장하여 읽기 속도를 높입니다."""
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "현재 등록된 지침 데이터가 없습니다."

@st.cache_resource
def get_gsheet():
    """구글 시트 연결을 유지합니다."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["google_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# --- 2. 화면 UI ---
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 학교시설개방 스마트 질의응답")
st.caption("안양과천 교육지원청의 시설개방 지침 및 예약 현황을 안내합니다.")

with st.form("qna_form"):
    user_question = st.text_area("궁금한 점을 입력하세요.", height=150, placeholder="예: 체육관 미개방 사유가 뭐야?")
    submitted = st.form_submit_button("질문하기")

    if submitted:
        if not user_question.strip():
            st.warning("질문을 입력해주세요.")
            st.stop()
        
        with st.spinner('지침을 확인 중입니다...'):
            try:
                # 최적화된 리소스 불러오기
                model = get_model()
                manual_context = load_manual_data()
                sheet = get_gsheet()
                
                # AI 답변 지침
                prompt = f"""당신은 안양과천교육지원청 시설개방 전문가입니다. 
아래 [데이터]를 근거로 답변하되, 데이터에 없는 내용은 행정실 문의를 안내하세요.

[데이터]
{manual_context}

[질문]: {user_question}"""

                # 답변 생성
                response = model.generate_content(prompt)
                answer = response.text
                
                st.info(answer)
                
                # 시트 기록
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([now, "익명", user_question, answer])
                st.success("✅ 답변 완료 및 기록되었습니다.")

            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ 사용량이 많습니다. 30초 뒤 다시 시도해주세요.")
                else:
                    st.error(f"오류 발생: {e}")
