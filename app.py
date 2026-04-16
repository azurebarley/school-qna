import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# --- 1. API 및 구글 시트 설정 (비밀 금고에서 가져오기) ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# JSON 파일 대신 스트림릿 비밀 금고에서 정보를 읽어옵니다.
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# '내가_만든_시트_이름'을 실제 구글 시트 이름으로 바꿔주세요. (예: 시설개방_질문취합)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit?gid=0#gid=0").sheet1 

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
        with st.spinner('답변을 찾고 있습니다...'):
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(f"{INSTRUCTION}\n\n질문: {user_question}")
            answer = response.text
            
            st.write("---")
            st.markdown(f"**AI 답변:**\n{answer}")
            
            # 구글 시트에 기록
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([now, school_name, user_question, answer])
            st.success("✅ 관리자 시트에 질문 내역이 자동 취합되었습니다.")
