import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

# --- 1. API 및 구글 시트 설정 ---
# secrets에서 제미나이 API 키를 가져와 설정합니다.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_authorized_model():
    """사용자의 API 키로 접근 가능한 최적의 모델(flash 또는 pro)을 자동으로 찾아 반환합니다."""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name or 'pro' in m.name:
                    return m.name
    except:
        pass
    return "models/gemini-1.5-flash" # 기본 권장 모델

# 구글 시트 인증 및 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# 주무관님의 구글 시트 주소를 직접 연결합니다.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit"
sheet = client.open_by_url(SHEET_URL).sheet1

# --- 2. 데이터 및 환경 설정 ---
def load_manual_data():
    """깃허브에 올린 매뉴얼.txt 파일을 읽어옵니다."""
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "현재 등록된 시설개방 지침 및 예약 현황 데이터가 없습니다."

# --- 3. 웹사이트 UI 구성 ---
st.set_page_config(page_title="시설개방 스마트 헬퍼", page_icon="🏫", layout="centered")

st.title("🏫 학교시설개방 스마트 질의응답")
st.markdown("""
안양과천 교육지원청의 **시설개방 지침** 및 **학교별 이용 가능 현황**에 대해 질문해주세요.  
예) *"오늘 저녁 7시에 비어있는 체육관 알려줘"*, *"시설개방 인센티브가 뭐야?"*
""")
st.write("---")

# 질문 입력 폼
with st.form("qna_form", clear_on_submit=False):
    # 학교명 입력 칸을 없애고 질문창만 크게 배치하여 편의성을 높였습니다.
    user_question = st.text_area("궁금한 점을 상세히 입력해주세요.", height=200, placeholder="여기에 질문을 입력하세요...")
    submitted = st.form_submit_button("질문하기")

    if submitted:
        if not user_question.strip():
            st.warning("질문을 입력하지 않으셨습니다.")
        else:
            with st.spinner('안양과천 교육지원청의 최신 지침과 현황을 확인하고 있습니다...'):
                try:
                    # 매뉴얼 및 예약 현황 데이터 로드
                    manual_context = load_manual_data()
                    
                    # 사용할 AI 모델 가져오기
                    target_model_name = get_authorized_model()
                    model = genai.GenerativeModel(target_model_name)
                    
                    # AI에게 줄 최종 지침(Prompt) - 이용자 없는 학교 위주 답변 지침 포함
                    full_instruction = f"""
당신은 안양과천교육지원청의 학교시설개방 업무를 보조하는 AI 전문가입니다.
제공된 [데이터]를 바탕으로 질문에 답변하세요.

[핵심 답변 원칙]
1. 이용 가능한 시설을 묻는 경우, [데이터]의 예약 현황을 분석하여 '현재 이용 단체가 없는 시간대'를 가진 학교를 우선적으로 추천하세요.
2. 특정 학교가 꽉 찼다면, 데이터 내에서 비어있는 인근 학교를 대안으로 제시하세요.
3. 지침에 명시된 '학교 자율 개방 원칙(강제 배정 불가)'을 항상 유념하여 답변하세요.
4. 데이터에 없는 상세 예약은 "해당 학교 행정실로 실시간 확인이 필요함"을 안내하세요.

[데이터]
{manual_context}

[질문]: {user_question}
"""
