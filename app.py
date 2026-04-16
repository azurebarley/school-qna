import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

# --- 1. API 및 구글 시트 설정 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1 

# --- 2. 매뉴얼 파일 읽기 함수 ---
def load_manual():
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "매뉴얼 정보를 찾을 수 없습니다."

# --- 3. 웹사이트 화면 구성 ---
st.title("🏫 시설개방 스마트 질의응답")

with st.form("qna_form"):
    school_name = st.text_input("소속 학교명을 입력해주세요 (예: 안양초)")
    user_question = st.text_area("궁금한 점을 상세히 적어주세요.")
    submitted = st.form_submit_button("질문하기")

    if submitted and user_question:
        with st.spinner('매뉴얼 지침을 확인 중입니다...'):
            try:
                # 매뉴얼 텍스트 불러오기
                manual_data = load_manual()
                
                # 사용 가능한 모델 자동 검색
                valid_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model = next((m for m in valid_models if "flash" in m), valid_models[0])
                
                model = genai.GenerativeModel(target_model)
                
                # 지침(Prompt) 구성
                full_prompt = f"""
당신은 안양과천교육지원청의 학교시설개방 업무 보조 AI입니다.
아래 제공되는 [매뉴얼 데이터]를 완벽히 숙지하고, 질문에 대해 이 근거에만 기반하여 답변하세요.

[매뉴얼 데이터]
{manual_data}

[질문자 학교명]: {school_name}
[질문]: {user_question}
"""
                response = model.generate_content(full_prompt)
                answer = response.text
                
                st.write("---")
                st.markdown(f"**AI 답변:**\n{answer}")
                
                # 구글 시트에 기록
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([now, school_name, user_question, answer])
                st.success(f"✅ 질문 내역이 취합되었습니다. (참조: 매뉴얼.txt)")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
