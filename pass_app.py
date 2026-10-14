import os
import re
import json
import html
import time

import streamlit as st
import pypdf
from google import genai
from google.genai import types

# =========================================================
# 프로젝트 주소 (URL)
# ---------------------------------------------------------
# 상단 바와 하단 푸터에 표시되는 주소입니다.
# Streamlit Cloud 배포 시 Custom subdomain을 pass-study 로 정하면 이 주소와 같아집니다.
# 다른 이름을 쓰게 되면 아래 PROJECT_URL 값만 실제 주소로 바꾸세요.
# =========================================================
PROJECT_URL = "https://pass-study.streamlit.app"
PROJECT_URL_SAFE = html.escape(PROJECT_URL, quote=True)
PROJECT_HOST = html.escape(PROJECT_URL.split("://", 1)[-1])

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="P.A.S.S. | PDF AI Study System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# HTML 렌더링 헬퍼
# ---------------------------------------------------------
# st.markdown(unsafe_allow_html=True)에 들여쓰기가 있는 문자열을
# 그대로 넘기면, 마크다운이 4칸 이상 들여쓰기를 "코드블록"으로
# 인식해서 <div> 태그가 그대로 텍스트로 출력되는 문제가 있음.
# 모든 줄의 앞뒤 공백/빈 줄을 제거한 뒤 렌더링해서 이 문제를 방지.
# =========================================================
def render(content: str):
    lines = [line.strip() for line in content.strip().split("\n")]
    lines = [line for line in lines if line != ""]
    st.markdown("\n".join(lines), unsafe_allow_html=True)


# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #f8faff 0%, #f1f4fa 100%);
    }

    .block-container {
        max-width: 1080px;
        padding-top: 0rem;
        padding-bottom: 4rem;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    .navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 28px;
        margin: 0 -1rem 10px -1rem;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid #e8ebf2;
        position: sticky;
        top: 0;
        z-index: 999;
    }

    .nav-left { display: flex; align-items: center; gap: 10px; }
    .nav-logo { font-size: 22px; font-weight: 900; color: #111827; letter-spacing: -0.5px; }
    .nav-logo span { color: #2563eb; }
    .nav-tagline {
        font-size: 12px; color: #9ca3af; font-weight: 500;
        border-left: 1px solid #e5e7eb; padding-left: 10px;
    }
    .nav-badge {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white; padding: 8px 16px; border-radius: 30px;
        font-size: 12px; font-weight: 700; letter-spacing: 0.3px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
    a.nav-badge { text-decoration: none; color: white !important; }
    a.nav-badge:hover { filter: brightness(1.08); }

    .footer-link { color: #2563eb !important; font-weight: 600; text-decoration: none; }
    .footer-link:hover { text-decoration: underline; }

    .hero { text-align: center; padding: 50px 20px 45px 20px; }
    .hero-pill {
        display: inline-block; background: #eaf2ff; color: #2563eb;
        padding: 6px 16px; border-radius: 20px; font-size: 12.5px;
        font-weight: 700; margin-bottom: 18px; letter-spacing: 0.2px;
    }
    .hero-title {
        font-size: 44px; font-weight: 900; color: #0f172a;
        letter-spacing: -1.2px; line-height: 1.25; margin-bottom: 14px;
    }
    .hero-title span {
        background: linear-gradient(135deg, #2563eb, #60a5fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-description {
        font-size: 16.5px; color: #6b7280; line-height: 1.8;
        max-width: 560px; margin: 0 auto;
    }

    .how-wrap { display: flex; gap: 16px; margin: 10px 0 45px 0; }
    .how-card {
        flex: 1; background: white; border: 1px solid #e8ebf2;
        border-radius: 18px; padding: 22px 18px; text-align: center;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    }
    .how-step {
        display: inline-flex; align-items: center; justify-content: center;
        width: 30px; height: 30px; border-radius: 50%; background: #0f172a;
        color: white; font-size: 13px; font-weight: 800; margin-bottom: 10px;
    }
    .how-icon { font-size: 26px; margin-bottom: 4px; }
    .how-title { font-weight: 700; color: #1f2937; font-size: 15px; margin-bottom: 4px; }
    .how-desc { color: #9ca3af; font-size: 12.5px; line-height: 1.5; }

    .section-title {
        font-size: 21px; font-weight: 800; color: #0f172a;
        margin-top: 8px; margin-bottom: 4px; letter-spacing: -0.3px;
    }
    .section-description { color: #8b93a1; font-size: 13.5px; margin-bottom: 18px; }

    .api-card {
        background: white; border: 1px solid #e8ebf2; border-radius: 18px;
        padding: 22px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(15,23,42,0.03);
    }

    .upload-card {
        background: white; border: 2px dashed #c7d2fe; border-radius: 20px;
        padding: 34px 20px; text-align: center; margin-bottom: 18px;
    }
    .upload-icon { font-size: 38px; margin-bottom: 8px; }
    .upload-title { font-size: 17px; font-weight: 700; color: #374151; }
    .upload-description { color: #9ca3af; font-size: 13.5px; margin-top: 4px; }

    .stat-card {
        background: white; border: 1px solid #e8ebf2; border-radius: 16px;
        padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(15,23,42,0.03);
    }
    .stat-number { font-size: 26px; font-weight: 850; color: #2563eb; letter-spacing: -0.5px; }
    .stat-label { color: #9ca3af; font-size: 12.5px; margin-top: 4px; font-weight: 600; }

    .summary-card {
        background: white; border: 1px solid #e8ebf2; border-radius: 20px;
        padding: 26px; box-shadow: 0 3px 14px rgba(15,23,42,0.04);
    }
    .summary-item {
        padding: 13px 0; border-bottom: 1px solid #f1f3f8;
        color: #374151; line-height: 1.6; font-size: 14.5px;
    }
    .summary-item:last-child { border-bottom: none; }
    .summary-number {
        display: inline-block; width: 26px; height: 26px; line-height: 26px;
        text-align: center; border-radius: 50%; background: #eaf2ff;
        color: #2563eb; font-size: 12px; font-weight: 800; margin-right: 10px;
    }

    .quiz-card {
        background: white; border: 1px solid #e8ebf2; border-radius: 20px;
        padding: 24px; margin-bottom: 16px; box-shadow: 0 3px 14px rgba(15,23,42,0.04);
    }
    .quiz-number {
        display: inline-block; background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white; border-radius: 8px; padding: 5px 11px; font-size: 11.5px;
        font-weight: 800; letter-spacing: 0.4px; margin-bottom: 12px;
    }
    .quiz-question { font-size: 16.5px; font-weight: 700; color: #1f2937; line-height: 1.6; }

    .score-card {
        background: linear-gradient(135deg, #0f172a, #1e3a8a);
        border-radius: 22px; text-align: center; padding: 38px;
        margin: 20px 0; color: white;
    }
    .score-label { color: #93c5fd; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
    .score-number { font-size: 54px; font-weight: 900; margin: 6px 0; }
    .score-description { color: #cbd5e1; font-size: 13.5px; }

    .wrong-card {
        background: #fffafa; border: 1px solid #fecaca; border-radius: 18px;
        padding: 20px; margin-bottom: 14px;
    }
    .wrong-title { font-weight: 700; color: #374151; line-height: 1.6; margin-bottom: 12px; }
    .wrong-answer { color: #dc2626; margin: 5px 0; font-size: 14px; }
    .correct-answer { color: #16a34a; margin: 5px 0; font-size: 14px; }

    .stButton > button { border-radius: 12px !important; font-weight: 700 !important; padding: 10px 0 !important; }

    .custom-footer { text-align: center; padding-top: 55px; color: #b0b7c3; font-size: 12.5px; line-height: 1.8; }
    .custom-footer b { color: #6b7280; }

</style>
""", unsafe_allow_html=True)


# =========================================================
# 네비게이션 바
# =========================================================
render(f"""
<div class="navbar">
    <div class="nav-left">
        <span class="nav-logo">📚 P.A.S.S<span>.</span></span>
        <span class="nav-tagline">PDF AI Study System</span>
    </div>
    <a class="nav-badge" href="{PROJECT_URL_SAFE}" target="_blank" rel="noopener noreferrer">🔗 {PROJECT_HOST}</a>
</div>
""")


# =========================================================
# Hero
# =========================================================
render("""
<div class="hero">
    <div class="hero-pill">🎓 캡스톤 프로젝트 · AI 학습 도우미</div>
    <div class="hero-title">PDF를 <span>똑똑하게</span> 공부하세요</div>
    <div class="hero-description">
        학습 자료를 업로드하면 Gemini AI가 핵심 내용을 정리하고<br>
        자료 기반 복습 퀴즈를 생성해 이해도를 확인할 수 있습니다.
    </div>
</div>
""")


# =========================================================
# 이용 방법
# =========================================================
render("""
<div class="how-wrap">
    <div class="how-card">
        <div class="how-step">1</div>
        <div class="how-icon">📄</div>
        <div class="how-title">PDF 업로드</div>
        <div class="how-desc">학습할 자료를 업로드하세요</div>
    </div>
    <div class="how-card">
        <div class="how-step">2</div>
        <div class="how-icon">🧠</div>
        <div class="how-title">AI 분석 & 요약</div>
        <div class="how-desc">핵심 내용을 자동으로 정리</div>
    </div>
    <div class="how-card">
        <div class="how-step">3</div>
        <div class="how-icon">📝</div>
        <div class="how-title">복습 퀴즈</div>
        <div class="how-desc">퀴즈를 풀며 이해도 점검</div>
    </div>
</div>
""")


# =========================================================
# API 설정
# ---------------------------------------------------------
# API 키는 코드에 직접 적지 않고 Streamlit secrets(또는 환경변수)에서 읽습니다.
#  - 로컬 실행: 프로젝트 폴더의 .streamlit/secrets.toml 에
#               GEMINI_API_KEY = "발급받은_키"  를 적어두세요.
#  - 배포(Streamlit Cloud): 앱 설정의 Secrets 칸에 같은 내용을 붙여넣으세요.
# 발급: https://aistudio.google.com/apikey
# =========================================================
GEMINI_MODEL = "gemini-3.8-flash"


def load_api_key() -> str:
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.environ.get("GEMINI_API_KEY", "")


api_key = load_api_key()


# =========================================================
# PDF 업로드
# =========================================================
st.markdown('<div class="section-title">📄 학습 자료 업로드</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">공부할 PDF 파일을 업로드해주세요.</div>', unsafe_allow_html=True)

render("""
<div class="upload-card">
    <div class="upload-icon">📄</div>
    <div class="upload-title">PDF 학습 자료</div>
    <div class="upload-description">PDF 파일을 업로드하고 AI 학습을 시작하세요.</div>
</div>
""")

uploaded_file = st.file_uploader(
    "PDF 파일 선택",
    type=["pdf"],
    label_visibility="collapsed"
)


# =========================================================
# 학습 설정
# =========================================================
st.markdown('<div class="section-title">⚙️ 학습 설정</div>', unsafe_allow_html=True)
st.markdown('<div class="section-description">원하는 퀴즈 난이도와 문제 수를 설정하세요.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    question_count = st.slider("📝 문제 수", min_value=3, max_value=10, value=5)

with col2:
    difficulty = st.selectbox("🎯 난이도", ["쉬움", "보통", "어려움"], index=1)


# =========================================================
# Gemini API 호출 함수
# =========================================================
MAX_SOURCE_CHARS = 12000  # 토큰/비용 관리를 위해 원문 앞부분만 사용

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "quizzes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING"},
                    "options": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "answer": {"type": "INTEGER"},
                    "explanation": {"type": "STRING"}
                },
                "required": ["question", "options", "answer", "explanation"]
            }
        }
    },
    "required": ["summary", "quizzes"]
}


def build_prompt(source_text: str, count: int, level: str) -> str:
    trimmed = source_text[:MAX_SOURCE_CHARS]
    truncated_note = "" if len(source_text) <= MAX_SOURCE_CHARS else "\n(※ 자료가 길어 앞부분 일부만 사용됨)"

    return f"""다음은 PDF 학습 자료에서 추출한 텍스트입니다.{truncated_note}
---
{trimmed}
---

위 자료를 바탕으로 아래 두 가지를 생성하세요.

1. summary: 이 자료의 핵심 내용을 요약한 문장 3~5개 (각 문장은 한국어로, 너무 짧지 않게).
2. quizzes: 난이도 "{level}"에 맞는 4지선다 객관식 퀴즈 정확히 {count}개.
   - 각 문제는 반드시 자료의 실제 내용에 기반해야 함 (자료에 없는 내용으로 문제를 내지 말 것).
   - options는 정확히 4개, 그 중 하나만 정답.
   - answer는 정답 옵션의 인덱스 (0부터 시작하는 정수).
   - explanation은 왜 그것이 정답인지 한두 문장으로 설명."""


def parse_json_response(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # JSON 객체 부분만 추출해서 재시도
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("AI 응답에서 JSON을 파싱할 수 없습니다.")


def generate_summary_and_quiz(api_key: str, model: str, source_text: str, count: int, level: str) -> dict:
    client = genai.Client(api_key=api_key)

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=build_prompt(source_text, count, level),
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "당신은 학습 자료를 분석해서 핵심 요약과 객관식 복습 퀴즈를 만드는 "
                        "AI 학습 도우미입니다. 반드시 지정된 JSON 스키마에 맞는 결과만 생성하세요."
                    ),
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    max_output_tokens=4000,
                )
            )
            break

        except Exception as e:
            error_message = str(e)

            if "503" in error_message or "UNAVAILABLE" in error_message:
                if attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)
                    time.sleep(wait_time)
                    continue

            raise

    raw_text = response.text
    if not raw_text:
        raise ValueError("AI로부터 빈 응답을 받았습니다.")

    data = parse_json_response(raw_text)

    if "summary" not in data or "quizzes" not in data:
        raise ValueError("AI 응답에 summary 또는 quizzes 항목이 없습니다.")

    return data


# =========================================================
# 분석 버튼
# =========================================================
st.markdown("")

if st.button("🚀 AI 학습 시작", use_container_width=True, type="primary"):

    if uploaded_file is None:
        st.warning("📄 먼저 PDF 파일을 업로드해주세요.")

    elif not api_key:
        st.warning("🔑 Gemini API 키가 설정되지 않았습니다. .streamlit/secrets.toml(배포 시에는 앱의 Secrets)에 GEMINI_API_KEY를 등록해주세요.")

    else:

        with st.spinner("PDF 내용을 추출하고 있습니다..."):
            reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            page_count = len(reader.pages)

        if not text.strip():
            st.error("⚠️ PDF에서 텍스트를 추출하지 못했습니다. 스캔본 이미지 PDF일 수 있습니다.")

        else:
            with st.spinner("Gemini AI가 자료를 분석하고 요약/퀴즈를 생성하고 있습니다..."):
                try:
                    result = generate_summary_and_quiz(
                        api_key=api_key,
                        model=GEMINI_MODEL,
                        source_text=text,
                        count=question_count,
                        level=difficulty
                    )

                    st.session_state["pdf_text"] = text
                    st.session_state["page_count"] = page_count
                    st.session_state["pdf_filename"] = uploaded_file.name
                    st.session_state["text_truncated"] = len(text) > MAX_SOURCE_CHARS
                    st.session_state["summary"] = result["summary"]
                    st.session_state["quizzes"] = result["quizzes"][:question_count]
                    st.session_state["analyzed"] = True
                    st.session_state["quiz_submitted"] = False
                    
                    st.session_state["used_question_count"] = question_count
                    st.session_state["used_difficulty"] = difficulty

                    # 이전 응답이 남아있지 않도록 라디오 선택 초기화
                    for i in range(10):
                        st.session_state.pop(f"answer_{i}", None)

                    st.success("✅ PDF 분석과 AI 퀴즈 생성이 완료되었습니다.")

                except ValueError as e:
                    st.error(f"⚠️ AI 응답을 처리하지 못했습니다: {e}")

                except Exception as e:
                    error_message = str(e)
                    if "API_KEY_INVALID" in error_message or "API key not valid" in error_message or "401" in error_message:
                        st.error("🔑 API 키가 올바르지 않습니다. 다시 확인해주세요.")
                    elif "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
                        st.error("⏳ 요청이 너무 많습니다. 잠시 후 다시 시도해주세요.")
                    else:
                        st.error(f"⚠️ Gemini API 호출 중 오류가 발생했습니다: {error_message}")


# =========================================================
# 분석 결과
# =========================================================
if st.session_state.get("analyzed", False):

    text = st.session_state["pdf_text"]
    page_count = st.session_state["page_count"]
    summary = st.session_state.get("summary", [])
    quizzes = st.session_state.get("quizzes", [])


    # =====================================================
    # PDF 정보
    # =====================================================
    st.markdown('<div class="section-title">📊 학습 자료 정보</div>', unsafe_allow_html=True)

    st.write(f"📄 파일명: {st.session_state.get('pdf_filename', '알 수 없음')}")
    if st.session_state.get("text_truncated", False):
        st.info(
            "ℹ️ PDF 내용이 길어 AI 분석에는 앞부분 12,000자가 사용되었습니다."
    )
    col1, col2, col3 = st.columns(3)

    with col1:
        render(f"""
        <div class="stat-card">
            <div class="stat-number">PDF</div>
            <div class="stat-label">학습 자료</div>
        </div>
        """)

    with col2:
        render(f"""
        <div class="stat-card">
            <div class="stat-number">{page_count}</div>
            <div class="stat-label">총 페이지</div>
        </div>
        """)

    with col3:
        render(f"""
        <div class="stat-card">
            <div class="stat-number">{len(quizzes)}</div>
            <div class="stat-label">생성 문제</div>
        </div>
        """)


    # =====================================================
    # 추출 텍스트
    # =====================================================
    with st.expander("🔍 추출된 PDF 내용 확인"):
        st.text_area("PDF 내용", text, height=250)


    # =====================================================
    # AI 핵심 요약
    # =====================================================
    st.markdown('<div class="section-title">📌 AI 핵심 요약</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-description">Gemini AI가 PDF 내용을 분석해 정리한 핵심 요약입니다.</div>', unsafe_allow_html=True)

    items_html = ""
    for index, item in enumerate(summary):
        items_html += f"""
        <div class="summary-item">
            <span class="summary-number">{index + 1}</span>
            {item}
        </div>
        """

    render(f'<div class="summary-card">{items_html}</div>')


    # =====================================================
    # 복습 퀴즈
    # =====================================================
    st.markdown('<div class="section-title">📝 AI 복습 퀴즈</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-description">학습한 내용을 직접 풀어보며 이해도를 확인하세요.</div>', unsafe_allow_html=True)

    for index, quiz in enumerate(quizzes):

        question_number = index + 1

        render(f"""
        <div class="quiz-card">
            <div class="quiz-number">QUESTION {question_number}</div>
            <div class="quiz-question">{quiz["question"]}</div>
        </div>
        """)

        st.radio(
            "답을 선택하세요.",
            quiz["options"],
            index=None,
            key=f"answer_{index}",
            label_visibility="collapsed",
            disabled=st.session_state.get("quiz_submitted", False)
        )


    # =====================================================
    # 채점
    # =====================================================
    # =====================================================
    # 채점
    # =====================================================
    if st.button("📊 전체 채점", use_container_width=True, type="primary"):
        unanswered = []

        # 답하지 않은 문제가 있는지 먼저 확인
        for index, quiz in enumerate(quizzes):
            user_answer = st.session_state.get(f"answer_{index}")

            if user_answer is None:
                unanswered.append(index + 1)

        # 미응답 문제가 있으면 채점하지 않음
        if unanswered:
            unanswered_text = ", ".join(f"Q{num}" for num in unanswered)
            st.warning(f"⚠️ 아직 답하지 않은 문제가 있습니다: {unanswered_text}")
            st.session_state["quiz_submitted"] = False

        else:
            score = 0
            wrong_answers = []

            for index, quiz in enumerate(quizzes):
                user_answer = st.session_state.get(f"answer_{index}")
                selected_index = quiz["options"].index(user_answer)

                if selected_index == quiz["answer"]:
                    score += 1
                else:
                    wrong_answers.append({
                        "question_number": index + 1,
                        "question": quiz["question"],
                        "user_answer": user_answer,
                        "correct_answer": quiz["options"][quiz["answer"]],
                        "explanation": quiz["explanation"]
                    })

            st.session_state["quiz_score"] = score
            st.session_state["wrong_answers"] = wrong_answers
            st.session_state["quiz_submitted"] = True


    # =====================================================
    # 결과
    # =====================================================
    if st.session_state.get("quiz_submitted", False):

        score = st.session_state["quiz_score"]

        st.markdown('<div class="section-title">📊 학습 결과</div>', unsafe_allow_html=True)

        render(f"""
        <div class="score-card">
            <div class="score-label">QUIZ SCORE</div>
            <div class="score-number">{score} / {len(quizzes)}</div>
            <div class="score-description">퀴즈 결과를 확인하고 부족한 내용을 복습해보세요.</div>
        </div>
        """)


        # =================================================
        # 문제별 결과
        # =================================================
        for index, quiz in enumerate(quizzes):

            user_answer = st.session_state.get(f"answer_{index}")

            if user_answer is None:
                st.warning(f"Q{index + 1}: 답변하지 않았습니다.")
                continue

            selected_index = quiz["options"].index(user_answer)

            if selected_index == quiz["answer"]:
                st.success(f"Q{index + 1} · ⭕ 정답")
            else:
                st.error(f"Q{index + 1} · ❌ 오답")
                st.write(f"정답: **{quiz['options'][quiz['answer']]}**")

            st.caption(f"해설 · {quiz['explanation']}")


        # =================================================
        # 오답 노트
        # =================================================
        wrong_answers = st.session_state.get("wrong_answers", [])

        st.markdown('<div class="section-title">📕 오답 노트</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-description">틀린 문제를 다시 확인하고 복습하세요.</div>', unsafe_allow_html=True)

        if len(wrong_answers) == 0:
            st.success("🎉 모든 문제를 맞혔습니다!")
        else:
            for wrong in wrong_answers:
                render(f"""
                <div class="wrong-card">
                    <div class="wrong-title">Q{wrong["question_number"]}. {wrong["question"]}</div>
                    <div class="wrong-answer">❌ 내 답 · {wrong["user_answer"]}</div>
                    <div class="correct-answer">⭕ 정답 · {wrong["correct_answer"]}</div>
                </div>
                """)
                st.info(f"💡 해설 · {wrong['explanation']}")

        # =================================================
        # 다시 풀기
        # =================================================
        if st.button("🔄 다시 풀기", use_container_width=True):
            st.session_state["quiz_submitted"] = False
            st.session_state.pop("quiz_score", None)
            st.session_state.pop("wrong_answers", None)

            for i in range(len(quizzes)):
                st.session_state.pop(f"answer_{i}", None)

            st.rerun()

    # =====================================================
    # 현재 설정
    # =====================================================
    st.divider()
    st.caption(
        f"현재 설정 · {st.session_state['used_question_count']}문제 "
        f"· 난이도 {st.session_state['used_difficulty']} "
        f"· 모델 {GEMINI_MODEL}"
    )


# =========================================================
# Footer
# =========================================================
render(f"""
<div class="custom-footer">
    <b>P.A.S.S.</b> · PDF AI Study System<br>
    Gemini AI 기반 PDF 학습 자료 요약 및 자동 복습 퀴즈 생성 플랫폼<br>
    <a class="footer-link" href="{PROJECT_URL_SAFE}" target="_blank" rel="noopener noreferrer">{PROJECT_HOST}</a>
</div>
""")
