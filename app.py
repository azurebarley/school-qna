import streamlit as st
from groq import Groq
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# ───────────────────────────────────────────
# 1. Groq API 설정
# ───────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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
    gc = gspread.authorize(creds)
    return gc.open_by_url(
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
    question = st.text_area("질문 내용을 입력하세요.", placeholder="예: 인덕원중 개방 현황이 어떻게 되나요?", height=150)
    submit = st.form_submit_button("질문하기", use_container_width=True)

if submit:
    if not question.strip():
        st.warning("⚠️ 질문을 입력해주세요.")
        st.stop()

    with st.spinner("지침서를 확인하며 답변을 생성 중입니다..."):
        try:
            manual = load_manual()
            system_prompt = f"""당신은 안양과천교육지원청 학교시설 개방 담당 AI 도우미입니다.

아래는 학교별 시설 개방 현황 데이터입니다.
데이터는 탭(\\t)으로 구분된 표 형식이며 열 순서는 다음과 같습니다:
학교명 | 개방시설 | 개방 요일 및 시간 | 매칭 동호회명 | 비고

[규칙]
1. 질문에 학교명이 언급되면 해당 학교의 행을 찾아 정확히 답변하세요.
2. 개방 시간, 시설 종류, 동호회 정보를 구체적으로 안내하세요.
3. 데이터에 해당 학교나 시설이 없을 때만 "해당 정보가 없습니다"라고 답하세요.
4. 반드시 데이터를 끝까지 꼼꼼히 확인한 후 답변하세요.
5. 답변은 한국어로, 표 형식이나 목록으로 보기 좋게 정리해주세요.

[시설 개방 현황 데이터]
{manual}"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            answer = response.choices[0].message.content

            # 답변 출력
            st.success("✅ 답변이 생성되었습니다.")
            st.markdown("### 📋 답변")
            st.markdown(answer)
            st.caption("사용 모델: llama-3.3-70b-versatile (Groq)")

            # 구글 시트에 기록
            try:
                sheet = get_sheet()
                sheet.append_row([question, answer])
            except Exception as sheet_err:
                st.warning(f"⚠️ 시트 저장 중 오류가 발생했습니다: {sheet_err}")

        except Exception as e:
            err = str(e)
            if "429" in err:
                st.error("⚠️ API 사용량이 일시적으로 초과되었습니다. 1~2분 후 다시 시도해주세요.")
            elif "401" in err:
                st.error("⚠️ GROQ_API_KEY가 올바르지 않습니다. Streamlit secrets를 확인해주세요.")
            else:
                st.error(f"오류가 발생했습니다: {err}")
