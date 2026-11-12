import base64
import io
import sys
import streamlit as st
import sympy as sp
from sympy.geometry import Point, Line, Circle, Polygon
from PIL import Image
from openai import OpenAI

st.set_page_config(page_title="전천후 멀티모달 수학 AI 에이전트", page_icon="📐", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stTextInput input, .stTextArea textarea { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 0.5rem; }
    .stButton button { background-color: #4f46e5; color: white; font-weight: 600; border-radius: 0.5rem; border: none; }
    .stButton button:hover { background-color: #4338ca; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧮 Math AI Agent")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")
    st.markdown("### 📥 문제 입력 방식")
    input_mode = st.radio("방식 선택", ["텍스트 직접 입력", "사진 파일 업로드", "카메라로 직접 촬영"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<p style='font-size: 0.75rem; color: #64748b;'>Engine: SymPy + GPT-4o Vision<br>© 2026 Math Agent v3.0</p>", unsafe_allow_html=True)

st.title("📐 전천후 멀티모달 수학 AI 에이전트")
st.markdown("방정식, 미적분, 행렬, 기하학 등 풀고 싶은 수학 문제를 입력하거나 사진을 찍어주세요. **AI 연습장**과 **자가 교정(Self-Correction)**을 거쳐 완벽한 해설을 제공합니다.")
st.markdown("---")

problem_input = ""
uploaded_image_data = None

if input_mode == "텍스트 직접 입력":
    problem_input = st.text_area("풀고 싶은 수학 문제를 자유롭게 입력하세요:", value="점 (0, 0)과 점 (3, 4)를 지나는 직선의 방정식을 구하시오.", height=100)
elif input_mode == "사진 파일 업로드":
    uploaded_file = st.file_uploader("수학 문제 사진을 선택하세요", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드한 문제 사진", use_container_width=True)
        uploaded_image_data = uploaded_file.getvalue()
elif input_mode == "카메라로 직접 촬영":
    camera_file = st.camera_input("수학 문제를 카메라에 비추고 촬영하세요")
    if camera_file is not None:
        st.image(camera_file, caption="촬영된 문제 사진", use_container_width=True)
        uploaded_image_data = camera_file.getvalue()

st.markdown("")

if st.button("🚀 에이전트 실행하기", use_container_width=True):
    if not api_key:
        st.error("⚠️ 사이드바에 OpenAI API 키를 먼저 입력해주세요!")
    else:
        client = OpenAI(api_key=api_key)
        
        if uploaded_image_data is not None:
            with st.spinner("👀 AI가 사진 속 수학 문제를 읽어내는 중..."):
                base64_image = base64.b64encode(uploaded_image_data).decode('utf-8')
                try:
                    vision_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "이 이미지 안에 있는 수학 문제를 빠짐없이 읽어서 텍스트 형태로만 적어주세요. 다른 설명은 하지 마세요."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }],
                        max_tokens=300
                    )
                    problem_input = vision_response.choices[0].message.content.strip()
                    st.info(f"🔍 **사진에서 추출된 문제:** {problem_input}")
                except Exception as e:
                    st.error(f"이미지 판독 에러: {e}")

        if not problem_input:
            st.warning("⚠️ 풀어볼 문제가 없습니다. 텍스트를 입력하거나 사진을 촬영해주세요!")
        else:
            execution_output = None
            
            with st.status("🧠 AI 연습장 작동 중 (검산 루프 및 기하·대수 분석)...", expanded=True) as scratchpad:
                prompt = f"""
                당신은 세계 최고 수준의 전천후 수학 AI 에이전트입니다. 아래 문제를 해결할 수 있는 파이썬 실행 코드를 작성하세요.
                
                [사용 가능한 공구 상자 및 규칙]
                - 대수/방정식/미적분/행렬: `sympy` (sp.solve, sp.diff, sp.integrate, sp.Matrix 등)
                - 기하학 (좌표, 도형, 직선, 원 등): `sympy.geometry`의 `Point`, `Line`, `Circle`, `Polygon` 등을 적극 활용하세요.
                - 최종 결과나 해답은 반드시 `print()` 문으로 출력하세요.
                - 오직 실행 가능한 파이썬 코드 블록(```python ... ```)만 출력하세요.
                
                [문제]: {problem_input}
                """
                
                max_retries = 3
                messages = [{"role": "user", "content": prompt}]
                
                for attempt in range(max_retries):
                    st.write(f"🔄 **[시도 {attempt + 1}회차] 코드 생성 및 검산 중...**")
                    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.0)
                    raw_content = response.choices[0].message.content
                    code_to_run = raw_content.replace("```python", "").replace("```", "").strip()
                    
                    st.code(code_to_run, language="python")
                    
                    try:
                        old_stdout = sys.stdout
                        new_stdout = io.StringIO()
                        sys.stdout = new_stdout
                        
                        local_vars = {"sp": sp, "Point": Point, "Line": Line, "Circle": Circle, "Polygon": Polygon}
                        exec(code_to_run, globals(), local_vars)
                        
                        sys.stdout = old_stdout
                        execution_output = new_stdout.getvalue().strip()
                        st.success(f"✨ 검산 성공! 결과값: {execution_output}")
                        break  
                    except Exception as e:
                        sys.stdout = old_stdout
                        error_msg = str(e)
                        st.warning(f"⚠️ 실행 에러 발생: {error_msg} -> **에이전트가 에러를 분석하고 코드를 수정합니다!**")
                        messages.append({"role": "assistant", "content": raw_content})
                        messages.append({"role": "user", "content": f"방금 실행한 코드에서 다음과 같은 에러가 발생했습니다: {error_msg}. 에러를 수정하여 올바른 파이썬 코드만 다시 작성해주세요."})

                if not execution_output:
                    st.error("⚠️ 최대 재시도 횟수 내에 문제를 해결하지 못했습니다.")
                
                scratchpad.update(label="✨ AI 연습장: 사고 과정 및 검산 완료!", state="complete", expanded=False)

            if execution_output:
                st.markdown("---")
                st.subheader("👩‍🏫 수학 선생님의 단계별 해설")
                
                explanation_prompt = f"""
                당신은 친절한 수학 선생님입니다. [문제]와 [계산된 정답]을 바탕으로 
                학생들이 이해하기 쉽게 논리적인 단계별 풀이 해설을 마크다운 형식으로 작성해주세요.
                [문제]: {problem_input}
                [계산된 정답]: {execution_output}
                """
                
                with st.spinner("선생님 페르소나 해설 작성 중..."):
                    exp_response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": explanation_prompt}], temperature=0.3)
                    st.markdown(exp_response.choices[0].message.content)
                
                st.markdown(f"""
                    <div style="background-color: #1e1b4b; border: 1px solid #6366f1; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
                        <strong style="color: #818cf8;">✨ 최종 정답:</strong> <span style="color: #f8fafc; font-family: monospace;">{execution_output}</span>
                    </div>
                """, unsafe_allow_html=True)
