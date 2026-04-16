import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- 1. API 및 구글 시트 설정 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# 구글 시트 연결
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1 

# --- 2. AI 지침 설정 ---
INSTRUCTION = """
당신은 안양과천교육지원청의 학교시설개방 업무 보조 AI입니다.
질문자가 시설개방 MOU 시즌2 관련 내용을 물어보면 친절하게 답변해주세요.
가장 중요한 원칙: 학교는 체육회 매칭 시스템을 무조건 일괄 적용받거나 강제 배정받는 것이 아닙니다. 각 학교의 실정과 상황에 따라 자율적으로 선호하는 방식을 선택할 수 있습니다. 이 점을 혼동하지 않도록 명확히 안내하세요.
"""

# --- 3. 웹사이트 화면 구성 ---
st.title("🏫 시설개방 스마트 질의응답")

with st.form("qna_form"):
    school_name = st.text_input("소속 학교명을 입력해주세요 (예: 안양초)")
    user_question = st.text_area("궁금한 점을 상세히 적어주세요.")
    submitted = st.form_submit_button("질문하기")

    if submitted and user_question:
        with st.spinner('안양과천교육지원청 지침을 확인하며 답변을 생성 중입니다...'):
            try:
                # 💡 마법의 코드: 내 열쇠로 쓸 수 있는 AI 이름표를 서버에서 직접 가져옵니다.
                valid_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        valid_models.append(m.name.replace("models/", ""))
                
                if not valid_models:
                    st.error("사용 가능한 AI 모델이 없습니다. API 키를 다시 확인해주세요.")
                    st.stop()
                    
                # 사용 가능한 목록 중 가장 똑똑한 모델을 자동으로 선택
                target_model = valid_models[0]
                for m_name in valid_models:
                    if "flash" in m_name:
                        target_model = m_name
                        break
                    elif "pro" in m_name:
                        target_model = m_name
                        
                # 🎯 자동으로 찾은 모델명으로 챗봇 실행!
                model = genai.GenerativeModel(target_model)
                response = model.generate_content(f"{INSTRUCTION}\n\n질문: {user_question}")
                answer = response.text
                
                st.write("---")
                st.markdown(f"**AI 답변:**\n{answer}")
                
                # 구글 시트에 기록
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([now, school_name, user_question, answer])
                
                # 어떤 AI가 답변했는지 화면에 슬쩍 보여줍니다.
                st.success(f"✅ 관리자 시트에 질문 내역이 자동 취합되었습니다. (답변 AI: {target_model})")
                
            except Exception as e:
                st.error("앗! AI 서버와 통신하는 중 문제가 발생했습니다.")
                st.warning(f"에러 상세 내용: {e}")
