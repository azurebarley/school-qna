import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# 1. 설정
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_authorized_model():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            if 'flash' in m.name or 'pro' in m.name: return m.name
    return "models/gemini-1.5-flash"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# 2. 화면 구성 (학교명 삭제)
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 시설개방 스마트 질의응답")
st.caption("안양과천교육지원청 시설개방 지침에 대해 무엇이든 물어보세요.")

with st.form("qna_form"):
    # 학교명 칸을 없애고 질문창만 크게 배치했습니다.
    question = st.text_area("궁금한 점을 상세히 적어주세요.", height=200)
    submit = st.form_submit_button("질문하기")

    if submit and question:
        with st.spinner("지침서를 확인 중입니다..."):
            try:
                model_name = get_authorized_model()
                model = genai.GenerativeModel(model_name)
                
                manual_content = open("매뉴얼.txt", "r", encoding="utf-8").read() if os.path.exists("매뉴얼.txt") else ""
                
                # AI 지침: 학교명을 안 써도 자연스럽게 대답하도록 유도
                prompt = f"당신은 시설개방 전문가입니다. 아래 지침을 근거로 답하세요.\n\n[지침]\n{manual_content}\n\n[질문]: {question}"
                
                response = model.generate_content(prompt)
                st.info(response.text)
                
                # 시트 기록: 학교명 칸에는 '익명'으로 기록
                sheet.append_row(["익명", question, response.text])
                st.success("✅ 답변 완료")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
