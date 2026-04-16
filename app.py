import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# 1. API 및 구글 시트 초기 설정
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_authorized_model():
    """현재 API 키로 사용 가능한 최적의 모델 이름을 찾아 반환합니다."""
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            # 주무관님 계정에서 쓸 수 있는 모델 중 flash나 pro가 들어간 것을 우선 선택
            if 'flash' in m.name or 'pro' in m.name:
                return m.name
    return "models/gemini-pro" # 기본값

# 구글 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# 2. 자료 불러오기 (매뉴얼.txt)
def load_data():
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "등록된 지침 자료가 없습니다."

# 3. 화면 UI
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 시설개방 스마트 질의응답")

with st.form("qna_form"):
    school = st.text_input("소속 학교명")
    question = st.text_area("궁금한 점을 상세히 적어주세요.")
    submit = st.form_submit_button("질문하기")

    if submit and question:
        with st.spinner("지침서를 확인하며 답변을 생성 중입니다..."):
            try:
                # 사용 가능한 모델 자동 매칭
                model_name = get_authorized_model()
                model = genai.GenerativeModel(model_name)
                
                # 지침 데이터 결합
                manual_content = load_data()
                prompt = f"당신은 안양과천교육지원청 AI입니다. 아래 지침을 근거로 답변하세요.\n\n[지침]\n{manual_content}\n\n[질문]: {question}"
                
                # 답변 생성 및 출력
                response = model.generate_content(prompt)
                st.info(response.text)
                
                # 시트 기록
                sheet.append_row([school, question, response.text])
                st.success(f"✅ 기록 완료 (사용 모델: {model_name})")
                
            except Exception as e:
                if "429" in str(e):
                    st.warning("⚠️ 현재 접속량이 많습니다. 10초 뒤에 다시 시도해주세요.")
                else:
                    st.error(f"오류가 발생했습니다: {e}")
