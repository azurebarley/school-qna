import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# 1. 제미나이 설정
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 구글 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# 3. 화면 구성
st.title("🏫 시설개방 스마트 질의응답")

with st.form("qna"):
    q = st.text_area("질문을 입력하세요.")
    if st.form_submit_button("질문하기"):
        try:
            # 매뉴얼 파일 읽기
            manual = ""
            if os.path.exists("매뉴얼.txt"):
                with open("매뉴얼.txt", "r", encoding="utf-8") as f:
                    manual = f.read()

            # 답변 생성
            prompt = f"지침서 내용:\n{manual}\n\n질문: {q}"
            ans = model.generate_content(prompt).text
            
            st.info(ans)
            sheet.append_row(["익명", q, ans]) # 시트 기록
            st.success("완료!")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
