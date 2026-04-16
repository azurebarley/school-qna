from oauth2client.service_account import ServiceAccountCredentials
import json, os

# 1. 설정 (무료에서 가장 넉넉한 1.5-flash 모델 사용)
# 1. API 및 구글 시트 초기 설정
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 구글 시트 연결
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

# 3. 매뉴얼 읽기
def get_manual():
# 2. 자료 불러오기 (매뉴얼.txt)
def load_data():
if os.path.exists("매뉴얼.txt"):
with open("매뉴얼.txt", "r", encoding="utf-8") as f:
return f.read()
    return "매뉴얼 자료가 없습니다."
    return "등록된 지침 자료가 없습니다."

# 4. 화면 구성
# 3. 화면 UI
st.set_page_config(page_title="시설개방 헬퍼", page_icon="🏫")
st.title("🏫 시설개방 스마트 질의응답")

with st.form("qna"):
    school = st.text_input("학교명")
    q = st.text_area("질문 내용을 입력하세요.")
    submitted = st.form_submit_button("질문하기")
with st.form("qna_form"):
    school = st.text_input("소속 학교명")
    question = st.text_area("궁금한 점을 상세히 적어주세요.")
    submit = st.form_submit_button("질문하기")

    if submitted:
        if not q:
            st.warning("질문을 입력해주세요.")
            st.stop()
        
        with st.spinner("AI가 답변을 생성 중입니다..."):
    if submit and question:
        with st.spinner("지침서를 확인하며 답변을 생성 중입니다..."):
try:
                # 지침 구성
                manual_text = get_manual()
                prompt = f"당신은 안양과천교육지원청 AI입니다. 아래 자료를 근거로 답하세요.\n\n[자료]\n{manual_text}\n\n[질문]: {q}"
                # 사용 가능한 모델 자동 매칭
                model_name = get_authorized_model()
                model = genai.GenerativeModel(model_name)
                
                # 지침 데이터 결합
                manual_content = load_data()
                prompt = f"당신은 안양과천교육지원청 AI입니다. 아래 지침을 근거로 답변하세요.\n\n[지침]\n{manual_content}\n\n[질문]: {question}"

                # 답변 생성
                res = model.generate_content(prompt)
                ans = res.text
                # 답변 생성 및 출력
                response = model.generate_content(prompt)
                st.info(response.text)

                st.info(ans)
                # 시트 기록
                sheet.append_row([school, question, response.text])
                st.success(f"✅ 기록 완료 (사용 모델: {model_name})")

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
                    st.warning("⚠️ 현재 접속량이 많습니다. 10초 뒤에 다시 시도해주세요.")
else:
st.error(f"오류가 발생했습니다: {e}")
