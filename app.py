from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

# --- 1. API 및 구글 시트 설정 ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
@@ -12,16 +13,14 @@
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
# --- 2. 매뉴얼 파일 읽기 함수 ---
def load_manual():
    if os.path.exists("매뉴얼.txt"):
        with open("매뉴얼.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "매뉴얼 정보를 찾을 수 없습니다."

# --- 3. 웹사이트 화면 구성 ---
st.title("🏫 시설개방 스마트 질의응답")
@@ -32,30 +31,29 @@
submitted = st.form_submit_button("질문하기")

if submitted and user_question:
        with st.spinner('안양과천교육지원청 지침을 확인하며 답변을 생성 중입니다...'):
        with st.spinner('매뉴얼 지침을 확인 중입니다...'):
try:
                # 💡 마법의 코드: 내 열쇠로 쓸 수 있는 AI 이름표를 서버에서 직접 가져옵니다.
                valid_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        valid_models.append(m.name.replace("models/", ""))
                # 매뉴얼 텍스트 불러오기
                manual_data = load_manual()
                
                # 사용 가능한 모델 자동 검색
                valid_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model = next((m for m in valid_models if "flash" in m), valid_models[0])

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
                
                # 지침(Prompt) 구성
                full_prompt = f"""
당신은 안양과천교육지원청의 학교시설개방 업무 보조 AI입니다.
아래 제공되는 [매뉴얼 데이터]를 완벽히 숙지하고, 질문에 대해 이 근거에만 기반하여 답변하세요.

[매뉴얼 데이터]
{manual_data}

[질문자 학교명]: {school_name}
[질문]: {user_question}
"""
                response = model.generate_content(full_prompt)
answer = response.text

st.write("---")
@@ -64,10 +62,7 @@
# 구글 시트에 기록
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
sheet.append_row([now, school_name, user_question, answer])
                
                # 어떤 AI가 답변했는지 화면에 슬쩍 보여줍니다.
                st.success(f"✅ 관리자 시트에 질문 내역이 자동 취합되었습니다. (답변 AI: {target_model})")
                st.success(f"✅ 질문 내역이 취합되었습니다. (참조: 매뉴얼.txt)")

except Exception as e:
                st.error("앗! AI 서버와 통신하는 중 문제가 발생했습니다.")
                st.warning(f"에러 상세 내용: {e}")
                st.error(f"오류가 발생했습니다: {e}")
