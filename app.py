import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os, time

# 1. 설정 (이름 자동 탐색 로직 포함)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_model_name():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            if 'flash' in m.name or 'pro' in m.name: return m.name
    return "models/gemini-1.5-flash"

# 구글 시트 연결
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# 2. UI 구성
st.title("🏫 시설개방 스마트 질의응답")
question = st.text_area("궁금한 점을 입력하세요.", height=150)

if st.button("질문하기"):
    if question:
        with st.spinner("지침 확인 중..."):
            # 매뉴얼 로드 (캐시 없이 직접 읽기)
            manual = open("매뉴얼.txt", "r", encoding="utf-8").read() if os.path.exists("매뉴얼.txt") else ""
            
            # 에러 발생 시 최대 2번 더 시도하는 로직
            for i in range(3): 
                try:
                    model = genai.GenerativeModel(get_model_name())
                    prompt = f"당신은 안양과천교육지원청 AI입니다. 아래 지침을 근거로 답하세요.\n\n[지침]\n{manual}\n\n[질문]: {question}"
                    
                    response = model.generate_content(prompt)
                    st.info(response.text)
                    sheet.append_row(["익명", question, response.text])
                    st.success("완료!")
                    break # 성공하면 반복문 탈출
                except Exception as e:
                    if "429" in str(e) and i < 2:
                        time.sleep(2) # 2초 쉬고 다시 시도
                        continue
                    st.error(f"오류: {e}")
                    break
