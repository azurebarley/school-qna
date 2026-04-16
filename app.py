import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# 1. 설정 (속도가 제일 빠른 flash 모델 고정)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 구글 시트 연결 (간소화)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# 3. 매뉴얼 읽기
def get_manual():
    return open("매뉴얼.txt", "r", encoding="utf-8").read() if os.path.exists("매뉴얼.txt") else "자료 없음"

# 4. 화면 구성 (깔끔하게)
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 시설개방 스마트 질의응답")

with st.form("qna"):
    school = st.text_input("학교명")
    q = st.text_area("질문 내용을 입력하세요.")
    if st.form_submit_button("질문하기"):
        if not q: st.stop()
        
        with st.spinner("답변 중..."):
            try:
                # 핵심 지침만 전달 (매뉴얼 데이터 포함)
                prompt = f"당신은 교육지원청 AI입니다. 아래 자료를 근거로 친절히 답하세요.\n\n[자료]\n{get_manual()}\n\n[질문]: {q}"
                ans = model.generate_content(prompt).text
                
                st.info(ans)
                sheet.append_row([school, q, ans]) # 시트 기록
                st.success("기록 완료!")
            except Exception as e:
                st.error("잠시 후 다시 시도해주세요. (초과 에러 방지)")
