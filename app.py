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
                
                # app.py 내 prompt 구성 부분 수정
prompt = f"""
당신은 시설개방 전문가입니다. 아래 지침과 이용 현황 데이터를 근거로 답변하세요.

[응대 원칙]
1. 이용 가능한 시설을 묻는 질문에는 반드시 '이용 중인 단체가 없는 시간대'가 있는 학교만 추천하세요.
2. 특정 학교의 예약이 꽉 차 있다면 그 사실을 알리고, 대신 비어있는 인근 학교를 제안하세요.
3. 데이터에 없는 내용은 "현재 실시간 예약 현황에 포함되어 있지 않으니 학교 행정실로 확인이 필요합니다"라고 안내하세요.

[지침 및 이용 현황 데이터]
{manual_content}

[질문]: {question}
"""
                response = model.generate_content(prompt)
                st.info(response.text)
                
                # 시트 기록: 학교명 칸에는 '익명'으로 기록
                sheet.append_row(["익명", question, response.text])
                st.success("✅ 답변 완료")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
