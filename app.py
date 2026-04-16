import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# 1. 설정 (무료에서 가장 넉넉한 1.5-flash 모델 사용)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 구글 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# 3. 매뉴얼 읽기
def get_manual():
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "매뉴얼 자료가 없습니다."

# 4. 화면 구성
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 시설개방 스마트 질의응답")

with st.form("qna"):
    school = st.text_input("학교명")
    q = st.text_area("질문 내용을 입력하세요.")
    submitted = st.form_submit_button("질문하기")

    if submitted:
        if not q:
            st.warning("질문을 입력해주세요.")
            st.stop()
        
        with st.spinner("AI가 답변을 생성 중입니다..."):
            try:
                # 지침 구성
                manual_text = get_manual()
                prompt = f"당신은 안양과천교육지원청 AI입니다. 아래 자료를 근거로 답하세요.\n\n[자료]\n{manual_text}\n\n[질문]: {q}"
                
                # 답변 생성
                res = model.generate_content(prompt)
                ans = res.text
                
                st.info(ans)
                
                # 시트 기록 (기록 실패해도 답변은 보여주도록 예외 처리)
                try:
                    sheet.append_row([school, q, ans])
                    st.success("✅ 질문이 관리자 시트에 기록되었습니다.")
                except:
                    st.warning("⚠️ 답변은 생성되었으나, 시트 기록에 실패했습니다.")
                    
            except Exception as e:
                # 에러 메시지를 구체적으로 확인하기 위해 다시 노출
                if "429" in str(e):
                    st.error("⚠️ 현재 무료 사용량이 일시적으로 초과되었습니다. 30초만 기다린 후 다시 눌러주세요.")
                else:
                    st.error(f"오류가 발생했습니다: {e}")
