import streamlit as st
from groq import Groq
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import re
import pandas as pd

# ───────────────────────────────────────────
# 1. Groq API 설정
# ───────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ───────────────────────────────────────────
# 2. 구글 시트 연결 (질문/답변 로그용 - 기존과 동일)
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
# 3. 학교 시설 데이터 + FAQ 불러오기
#    -> "시설개방_챗봇데이터.xlsx" 한 파일 안에 시트 두 개
#       · 학교데이터 : 학교명 | 운동장_개방방법 | 운동장_요일시간 | 운동장_이용동호회 |
#                      체육관_개방방법 | 체육관_요일시간 | 체육관_이용동호회 |

#       · FAQ        : 질문 | 답변
#    FAQ는 엑셀에서 행만 추가하면 코드 수정 없이 바로 반영됩니다.
# ───────────────────────────────────────────
DATA_FILE = "facility_chatbot_data.xlsx"


def _make_aliases(school_name: str) -> set:
    """'인덕원중학교' -> {'인덕원중학교', '인덕원중'} 같은 축약 별칭 생성.
    초/중/고 급을 구분해 동명 학교(인덕원초/중/고 등) 오매칭을 방지."""
    aliases = {school_name}
    for full, abbr in [("초등학교", "초"), ("중학교", "중"), ("고등학교", "고")]:
        if school_name.endswith(full):
            aliases.add(school_name[: -len(full)] + abbr)
    return aliases


@st.cache_data
def load_school_data():
    df = pd.read_excel(DATA_FILE, sheet_name="학교데이터").fillna("")
    df["_검색키"] = df["학교명"].astype(str).str.replace(" ", "", regex=False)
    return df


@st.cache_data
def build_alias_index(df: pd.DataFrame):
    """(별칭, 행 인덱스) 목록을 별칭이 긴 것부터 정렬해 반환.
    긴 별칭을 먼저 검사해야 '안양서초'와 '안양서중' 같은 비슷한 이름이 안 섞임."""
    if df.empty:
        return []
    pairs = []
    for idx, key in df["_검색키"].items():
        for alias in _make_aliases(key):
            pairs.append((alias, idx))
    pairs.sort(key=lambda x: -len(x[0]))
    return pairs


@st.cache_data
def load_faq():
    df = pd.read_excel(DATA_FILE, sheet_name="FAQ").fillna("")
    return df


def find_school(df: pd.DataFrame, alias_index: list, user_text: str):
    """질문 문장에서 학교명을 찾아 해당 행을 반환 (없으면 None).
    '관양초'처럼 줄임말로 물어봐도 매칭되며, 초/중/고 급을 구분해
    동명 학교(인덕원초/중/고 등)를 정확히 구분한다."""
    if df.empty or not alias_index:
        return None

    q = user_text.replace(" ", "")
    for alias, idx in alias_index:
        if alias and alias in q:
            return df.loc[idx]
    return None


def build_school_context(row) -> str:
    """해당 학교 1개 행만 압축한 컨텍스트. 전체 표 대신 이것만 프롬프트에 포함."""
    def or_none(v):
        return v if str(v).strip() else "정보 없음"

    note = or_none(row["비고"]) if "비고" in row.index else "정보 없음"

    return (
        f"[{row['학교명']} 시설개방 현황]\n"
        f"- 운동장: {or_none(row['운동장_개방방법'])} | "
        f"{or_none(row['운동장_요일시간'])} | "
        f"이용 동호회: {or_none(row['운동장_이용동호회'])}\n"
        f"- 체육관: {or_none(row['체육관_개방방법'])} | "
        f"{or_none(row['체육관_요일시간'])} | "
        f"이용 동호회: {or_none(row['체육관_이용동호회'])}\n"
    )


def build_faq_context(faq_df: pd.DataFrame) -> str:
    """FAQ는 보통 분량이 적어 전체를 그대로 포함."""
    if faq_df.empty:
        return "등록된 FAQ가 없습니다."

    lines = []
    for _, row in faq_df.iterrows():
        q = str(row.get("질문", "")).strip()
        a = str(row.get("답변", "")).strip()
        if q:
            lines.append(f"Q: {q}\nA: {a}")
    return "\n\n".join(lines) if lines else "등록된 FAQ가 없습니다."


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

    with st.spinner("데이터를 확인하며 답변을 생성 중입니다..."):
        try:
            try:
                school_df = load_school_data()
                faq_df = load_faq()
            except Exception as data_err:
                st.error(
                    f"⚠️ 데이터 파일을 읽지 못했습니다: {data_err}\n\n"
                    f"GitHub 저장소에 '{DATA_FILE}' 이름의 파일이 정확히 있는지, "
                    f"시트 이름이 '학교데이터' / 'FAQ'인지 확인해주세요."
                )
                st.stop()

            if school_df.empty:
                st.error(f"⚠️ '{DATA_FILE}'의 학교데이터 시트가 비어 있습니다. 파일을 확인해주세요.")
                st.stop()

            alias_index = build_alias_index(school_df)

            matched_row = find_school(school_df, alias_index, question)
            if matched_row is not None:
                school_context = build_school_context(matched_row)
            else:
                school_context = "질문에서 특정 학교명을 인식하지 못했습니다. 학교 관련 질문이라면 정확한 학교명을 다시 요청하세요."

            faq_context = build_faq_context(faq_df)

            system_prompt = f"""당신은 안양과천교육지원청 학교시설 개방 담당 AI 도우미입니다.

[규칙]
1. 질문에 학교명이 언급되면 아래 "학교 시설 데이터"를 근거로정확히 답변하세요.
2. 학교 시설과 무관한 일반적인 질문(매칭 제도, 신청 방법 등)은 아래 "FAQ"를 근거로 답변하세요.
3. 개방 시간, 시설 종류, 동호회 정보를 구체적으로 안내하세요.
4. 아래 자료에 해당 내용이 없을 때만 "해당 정보가 없습니다"라고 답하세요. 추측해서 답변하지 마세요.
5. 학교명이 인식되지 않았다는 안내가 보이면, 사용자에게 정확한 학교명을 알려달라고 요청하세요.
6. 답변은 한국어로, 표 형식이나 목록으로 보기 좋게 정리해주세요.
7. [빈 시간 계산 3단계 규칙] (물어볼 때만 답하고, 반드시 지킬 것) (빈 시간, 예약 가능한 시간 등)
① 개방시간 확인: 데이터의 '요일시간(개방 시간)'에 적힌 시간만 '학교가 문을 연 시간'입니다. 데이터에 없는 요일이나 시간(예: 월~토요일 전체, 새벽, 밤 등)은 '폐쇄' 상태이므로 절대 빈 시간으로 언급하지 마세요.
② 사용시간 차감: 1단계에서 확인된 개방 시간에서 '이용 동호회'가 사용 중인 시간을 정확히 뺍니다.
③ 결과 출력: 빼고 남은 시간이 있다면 그 시간만 안내하세요. 만약 남는 시간이 아예 없다면 억지로 지어내지 말고, "현재 개방되는 시간은 모두 동호회가 이용 중이므로 비어있는 시간이 없습니다."라고만 답변하세요.

[FAQ]
{faq_context}

[학교 시설 데이터]
{school_context}"""

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
            answer = answer.replace("~", r"\~")

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