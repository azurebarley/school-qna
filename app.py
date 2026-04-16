import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# ───────────────────────────────────────────
# 1. API 설정
# ───────────────────────────────────────────
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def get_model():
    """사용 가능한 Gemini 모델을 자동으로 탐색합니다."""
    try:
        available = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        # 우선순위: 2.0-flash → 1.5-flash → 1.5-pro → 첫 번째 모델
        priority = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        for pref in priority:
            found = next((m for m in available if pref in m), None)
            if found:
                return found
        return available[0] if available else "models/gemini-2.0-flash"
    except Exception:
        return "models/gemini-2.0-flash"

# ───────────────────────────────────────────
# 2. 구글 시트 연결
# ───────────────────────────────────────────
@st.cache_resource
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(st.secrets["google_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1CDnTXib4J3C0QYrCKIMUcbZoS6Olez4Pkq3ltOJSH9U/edit"
    ).sheet1

# ───────────────────────────────────────────
# 3. 매뉴얼 불러오기
# ───────────────────────────────────────────
def load_manual():
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "등록된 지침 자료가 없습니다."

# ───────────────────────────────────────────
# 4. UI
# ───────────────────────────────────────────
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 시설개방 스마트 질의응답")
st.caption("안양과천교육지원청 시설개방 관련 질문에 AI가 답변드립니다.")

with st.form("qna_form"):
    school = st.text_input("소속 학교명", placeholder="예: 안양초등학교")
    question = st.text_area("질문 내용을 입력하세요.", placeholder="예: 인덕원중 개방 현황이 어떻게 되나요?", height=150)
    submit = st.form_submit_button("질문하기", use_container_width=True)

if submit:
    if not school.strip():
        st.warning("⚠️ 학교명을 입력해주세요.")
        st.stop()
    if not question.strip():
        st.warning("⚠️ 질문을 입력해주세요.")
        st.stop()

    with st.spinner("지침서를 확인하며 답변을 생성 중입니다..."):
        try:
            model_name = get_model()
            model = genai.GenerativeModel(model_name)

            manual = load_manual()
            prompt = f"""당신은 안양과천교육지원청 시설개방 담당 AI 도우미입니다.
아래 지침을 근거로 질문에 성실하게 답변하세요.
지침에 없는 내용은 "지침서에서 확인되지 않는 내용입니다."라고 안내하세요.

[지침]
{manual}

[질문]
{question}"""

            response = model.generate_content(prompt)
            answer = response.text

            # 답변 출력
            st.success("✅ 답변이 생성되었습니다.")
            st.markdown("### 📋 답변")
            st.info(answer)
            st.caption(f"사용 모델: {model_name}")

            # 구글 시트에 기록
            try:
                sheet = get_sheet()
                sheet.append_row([school, question, answer])
            except Exception as sheet_err:
                st.warning(f"⚠️ 시트 저장 중 오류가 발생했습니다: {sheet_err}")

        except Exception as e:
            err = str(e)
            if "429" in err:
                st.error("⚠️ API 사용량이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "404" in err:
                st.error("⚠️ 사용 가능한 AI 모델을 찾을 수 없습니다. API 키를 확인해주세요.")
            elif "403" in err:
                st.error("⚠️ API 키 권한이 없습니다. Gemini API 키를 확인해주세요.")
            else:
                st.error(f"오류가 발생했습니다: {err}")
