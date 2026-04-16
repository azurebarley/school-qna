import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os, time

# --- 1. API 및 모델 설정 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 구글 시트 연결
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# --- 2. UI 구성 ---
st.title("🏫 시설개방 스마트 질의응답")
question = st.text_area("궁금한 점을 상세히 입력하세요.", height=150)

if st.button("질문하기"):
    if not question.strip():
        st.warning("질문을 입력해주세요.")
    else:
        with st.spinner("지침서를 확인 중입니다..."):
            manual_text = open("매뉴얼.txt", "r", encoding="utf-8").read() if os.path.exists("매뉴얼.txt") else ""
            
            # 404 오류를 피하기 위한 모델 명칭 후보군
            model_candidates = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-pro"]
            success = False

            for model_name in model_candidates:
                try:
                    model = genai.GenerativeModel(model_name)
                    prompt = f"당신은 안양과천교육지원청 AI입니다. 아래 지침을 근거로 답변하세요.\n\n[지침]\n{manual_text}\n\n[질문]: {question}"
                    
                    response = model.generate_content(prompt)
                    st.info(response.text)
                    
                    # 시트 기록
                    sheet.append_row(["익명", question, response.text])
                    st.success(f"✅ 답변 완료 (사용된 모델명: {model_name})")
                    success = True
                    break # 성공 시 루프 탈출
                except Exception as e:
                    # 404나 429 에러가 나면 다음 후보로 넘어감
                    continue
            
            if not success:
                st.error("현재 구글 API 서버와의 연결이 원활하지 않습니다. 잠시 후 스트림릿 페이지를 새로고침(F5)하고 다시 시도해 주세요.")
