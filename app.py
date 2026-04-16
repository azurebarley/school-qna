import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os, time

# --- 1. API 및 모델 설정 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_stable_model():
    """사용 가능한 모델 중 1.5-flash의 '전체 경로'를 정확히 찾아 반환합니다."""
    try:
        for m in genai.list_models():
            # 404 방지를 위해 서버가 제공하는 전체 이름(예: models/gemini-1.5-flash)을 그대로 사용
            if 'gemini-1.5-flash' in m.name and 'generateContent' in m.supported_generation_methods:
                return m.name
    except:
        pass
    return "models/gemini-1.5-flash" # 찾지 못할 경우 기본값

# 구글 시트 연결
creds_dict = json.loads(st.secrets["google_credentials"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit").sheet1

# --- 2. UI 구성 ---
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 시설개방 스마트 질의응답")

question = st.text_area("궁금한 점을 상세히 입력하세요.", height=150, placeholder="여기에 질문을 입력하세요...")

if st.button("질문하기"):
    if not question.strip():
        st.warning("질문을 입력해주세요.")
    else:
        with st.spinner("지침서를 확인 중입니다..."):
            # 800줄의 매뉴얼 로드
            manual_text = open("매뉴얼.txt", "r", encoding="utf-8").read() if os.path.exists("매뉴얼.txt") else ""
            
            # 에러 발생 시 재시도 로직
            for attempt in range(2):
                try:
                    target_model = get_stable_model()
                    model = genai.GenerativeModel(target_model)
                    
                    # 800줄을 읽어야 하므로 지침을 아주 명확하게 전달
                    prompt = f"당신은 안양과천교육지원청 AI입니다. 아래 지침을 근거로 답변하세요.\n\n[지침]\n{manual_text}\n\n[질문]: {question}"
                    
                    response = model.generate_content(prompt)
                    st.info(response.text)
                    
                    # 시트 기록
                    sheet.append_row(["익명", question, response.text])
                    st.success(f"✅ 답변 완료 (모델: {target_model})")
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg:
                        if attempt == 0:
                            st.warning("⚠️ 일시적으로 사용량이 많습니다. 5초 후 자동으로 재시도합니다...")
                            time.sleep(5)
                            continue
                        else:
                            st.error("⚠️ 오늘 또는 이번 분의 사용량이 모두 소진되었습니다. 잠시 후 다시 이용해주세요.")
                    elif "404" in error_msg:
                        st.error("⚠️ 모델 명칭 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
                    else:
                        st.error(f"오류가 발생했습니다: {e}")
                    break
