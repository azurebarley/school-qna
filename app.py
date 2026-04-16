import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# 1. API 설정 (과거에 가장 잘 작동하던 gemini-pro 모델로 고정)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# 모델명을 'gemini-pro'로 변경합니다. 이 명칭은 v1beta에서도 가장 잘 인식됩니다.
model = genai.GenerativeModel('gemini-pro')

# 2. 구글 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# 3. 화면 UI
st.title("🏫 시설개방 스마트 질의응답")

# 질문 입력창 (단일 입력)
user_question = st.text_area("궁금한 점을 상세히 입력하세요.", height=200)

if st.button("질문하기"):
    if user_question:
        with st.spinner('답변을 생성 중입니다...'):
            try:
                # 매뉴얼 파일 로드
                manual_text = ""
                if os.path.exists("매뉴얼.txt"):
                    with open("매뉴얼.txt", "r", encoding="utf-8") as f:
                        manual_text = f.read()

                # 지침 결합
                prompt = f"당신은 교육청 시설개방 업무 지원 AI입니다. 아래 지침을 보고 답하세요.\n\n[지침]\n{manual_text}\n\n[질문]: {user_question}"
                
                # 답변 생성
                response = model.generate_content(prompt)
                st.info(response.text)
                
                # 시트 기록
                sheet.append_row(["익명", user_question, response.text])
                st.success("✅ 완료되었습니다.")
                
            except Exception as e:
                # 에러 발생 시 원본 메시지 출력
                st.error(f"오류가 발생했습니다: {e}")
