import io
import json
import time
import streamlit as st
from groq import Groq
from gtts import gTTS

# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL Y ESTILOS CSS (DISEÑO EXACTO)
# ---------------------------------------------------------
st.set_page_config(page_title="Talento 360", page_icon="🎯", layout="centered", initial_sidebar_state="collapsed")

# Inyección de CSS global para replicar el diseño exacto
st.markdown("""
<style>
    /* Fondo completamente negro */
    .stApp { background-color: #000000 !important; color: #ffffff !important; font-family: sans-serif; }
    
    /* Hacer el encabezado transparente y la flecha blanca */
    header { background-color: transparent !important; }
    header button, header svg { color: white !important; fill: white !important; }
    
    /* Título principal superior izquierdo */
    .main-title { font-family: Impact, sans-serif; font-size: 32px; font-weight: bold; color: #ffffff; margin-top: -60px; margin-bottom: 20px; }
    
    /* Campos de texto y selecciones grises */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        background-color: #666666 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #cccccc !important;
    }
    
    /* Botones primarios */
    .stButton > button {
        background-color: #0B1340 !important;
        color: white !important;
        border: 2px solid white !important;
        border-radius: 25px !important;
        padding: 10px 30px !important;
        display: block;
        margin: 20px auto !important;
    }
    .stButton > button:hover {
        border-color: #8A2BE2 !important;
        color: #8A2BE2 !important;
    }
</style>
""", unsafe_allow_html=True)

MODEL_TEXT = "openai/gpt-oss-120b"
MODEL_STT = "whisper-large-v3-turbo"

# Barra lateral (oculta por defecto para no romper el diseño)
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Groq API Key", type="password")
    voice_on = st.toggle("🔊 Activar audio", value=True)

# Estado de la sesión
defaults = {
    "step": "welcome",
    "user_name": "",
    "history": [],
    "current_q": 1,
    "max_q": 3,
    "role": "",
    "level": "Junior",
    "job_desc": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if not api_key:
    st.title("TALENTO 360")
    st.warning("Abre el menú lateral (flecha arriba a la izquierda) e ingresa tu Groq API Key para comenzar.")
    st.stop()

client = Groq(api_key=api_key)

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
def text_to_speech(text: str) -> bytes:
    buffer = io.BytesIO()
    gTTS(text=text, lang="es").write_to_fp(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def ask_llm(messages, json_mode=False) -> str:
    kwargs = {"model": MODEL_TEXT, "messages": messages, "temperature": 0.7}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()

def transcribe(audio_file) -> str:
    result = client.audio.transcriptions.create(
        file=("respuesta.wav", audio_file.getvalue()),
        model=MODEL_STT,
        language="es",
    )
    return result.text.strip()

def generate_question() -> str:
    system_prompt = (
        f"Tu nombre es Ana Lucia C., una reclutadora de la institución 'Talento 360'. "
        f"Estás entrevistando a {st.session_state.user_name} para el puesto '{st.session_state.role}' (nivel {st.session_state.level}). "
        f"Descripción del puesto: {st.session_state.job_desc or 'No proporcionada'}. "
        "Haz UNA sola pregunta clara y directa. Alterna entre habilidades blandas y técnicas. "
        "Si es la primera pregunta, preséntate brevemente diciendo: 'Hola [Nombre], soy Ana, reclutadora de la institución. ¿Podrías...' "
        "Si no es la primera, ve directo a la pregunta sin volver a saludar. No repitas preguntas."
    )
    messages = [{"role": "system", "content": system_prompt}]
    for item in st.session_state.history:
        if item["question"]:
            messages.append({"role": "assistant", "content": item["question"]})
        if item["answer"]:
            messages.append({"role": "user", "content": item["answer"]})
    if not st.session_state.history:
        messages.append({"role": "user", "content": "Inicia la entrevista presentándote y haciendo la primera pregunta."})
    return ask_llm(messages)

def restart():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.markdown('<div class="main-title">TALENTO 360</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# PASO 1: PANTALLA DE BIENVENIDA SECUENCIAL
# ---------------------------------------------------------
if st.session_state.step == "welcome":
    st.markdown("<h2 style='text-align: center; margin-top: 25vh;'>Es un placer ayudarte en esta nueva etapa</h2>", unsafe_allow_html=True)
    time.sleep(2.5)
    st.session_state.step = "name"
    st.rerun()

# ---------------------------------------------------------
# PASO 2: INGRESO DE NOMBRE (Borde Morado)
# ---------------------------------------------------------
elif st.session_state.step == "name":
    st.markdown("<style>div[data-testid='stVerticalBlockBorderWrapper'] { border: 2px solid #8A2BE2 !important; background-color: #0B1340 !important; border-radius: 15px; margin-top: 10vh; }</style>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>Podrías decirme tu nombre</h3>", unsafe_allow_html=True)
        user_name = st.text_input("Nombre", label_visibility="collapsed", placeholder="Ingresa aqui tu nombre")
        if st.button("Continuar"):
            if user_name.strip():
                st.session_state.user_name = user_name.strip()
                st.session_state.step = "setup"
                st.rerun()

# ---------------------------------------------------------
# PASO 3: CONFIGURACIÓN (Borde Blanco)
# ---------------------------------------------------------
elif st.session_state.step == "setup":
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Responde estas preguntas antes de iniciar</h3>", unsafe_allow_html=True)
    st.markdown("<style>div[data-testid='stVerticalBlockBorderWrapper'] { border: 2px solid #ffffff !important; background-color: #0B1340 !important; border-radius: 15px; }</style>", unsafe_allow_html=True)
    
    with st.container(border=True):
        role = st.text_input("¿Cual es el nombre del cargo al que aspiras", placeholder="Ej. Desarrollador Frontend, Diseñador UX...")
        level = st.selectbox("¿Cuál es tu nivel de experiencia?", ["Junior", "Mid-Level", "Senior", "Líder / Manager"])
        job_desc = st.text_area("Descripcion de la oferta", placeholder="Pega aqui los requisitos del trabajo para preguntas mas precisas.")
        num_q = st.slider("¿Cuantas preguntas deseas responder?", 2, 5, 3)
    
    if st.button("Iniciar la simulacion"):
        if role.strip():
            st.session_state.role = role.strip()
            st.session_state.level = level
            st.session_state.job_desc = job_desc.strip()
            st.session_state.max_q = num_q
            st.session_state.current_q = 1
            st.session_state.step = "interview"
            st.rerun()

# ---------------------------------------------------------
# PASO 4: SIMULACIÓN DE ENTREVISTA (Borde Morado)
# ---------------------------------------------------------
elif st.session_state.step == "interview":
    q_num = st.session_state.current_q
    max_q = st.session_state.max_q
    idx = q_num - 1

    # Forzamos borde morado y text-area con contorno morado para este paso
    st.markdown("""
    <style>
        div[data-testid='stVerticalBlockBorderWrapper'] { border: 2px solid #8A2BE2 !important; background-color: #0B1340 !important; border-radius: 15px; }
        .stTextArea textarea { border: 2px solid #8A2BE2 !important; }
    </style>
    """, unsafe_allow_html=True)

    if len(st.session_state.history) < q_num:
        with st.spinner("Ana está formulando su pregunta..."):
            question = generate_question()
            audio = text_to_speech(question) if voice_on else None
            st.session_state.history.append({"question": question, "answer": "", "audio": audio, "new": True})

    item = st.session_state.history[idx]

    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>Ana Lucia C. (Reclutadora Talento 360)</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 18px; margin-top: 15px;'>{item['question']}</p>", unsafe_allow_html=True)
        
        if item.get("audio"):
            st.audio(item["audio"], format="audio/mp3", autoplay=item.get("new", False))
            item["new"] = False 

        tab_text, tab_voice = st.tabs(["Tu respuesta", "Respuesta por voz"])
        with tab_text:
            typed = st.text_area("Tu respuesta", label_visibility="collapsed", placeholder="Escribe aqui tu respuesta", key=f"txt_{idx}", height=100)
        with tab_voice:
            recording = st.audio_input("Graba tu respuesta", label_visibility="collapsed", key=f"rec_{idx}")

    if st.button("Enviar y continuar"):
        answer = typed.strip()
        if not answer and recording is not None:
            with st.spinner("Transcribiendo..."):
                answer = transcribe(recording)
        if answer:
            item["answer"] = answer
            if q_num < max_q:
                st.session_state.current_q += 1
            else:
                st.session_state.step = "evaluation"
            st.rerun()

# ---------------------------------------------------------
# PASO 5: REPORTE DE EVALUACIÓN (Borde Morado, Audio Completo)
# ---------------------------------------------------------
elif st.session_state.step == "evaluation":
    st.markdown("<style>div[data-testid='stVerticalBlockBorderWrapper'] { border: 2px solid #8A2BE2 !important; background-color: #0B1340 !important; border-radius: 15px; }</style>", unsafe_allow_html=True)

    transcript = "\n".join(f"Pregunta: {h['question']}\nRespuesta de {st.session_state.user_name}: {h['answer']}" for h in st.session_state.history)

    prompt = f"""
Evalúa esta entrevista para el puesto {st.session_state.role}.
Transcripción:
{transcript}
Responde SOLO con JSON:
{{
  "score_general": <entero 1 a 10>,
  "puntos_fuertes": ["<texto breve>", "<texto breve>", "<texto breve>"],
  "areas_mejora": ["<texto breve>", "<texto breve>", "<texto breve>"],
  "ejemplo_optimizacion": "<reescribe la respuesta más débil como 'Situación: ... Tarea: ... Acción: ... Resultado: ...'>"
}}
"""
    if "eval_data" not in st.session_state:
        with st.spinner("Ana está preparando tus resultados..."):
            raw = ask_llm([{"role": "user", "content": prompt}], json_mode=True)
            try:
                st.session_state.eval_data = json.loads(raw)
            except json.JSONDecodeError:
                st.error("Error al generar resultados. Intenta de nuevo.")
                st.stop()

    data = st.session_state.eval_data
    score = data.get("score_general", 0)
    fuertes = data.get("puntos_fuertes", [])
    mejoras = data.get("areas_mejora", [])
    ejemplo = data.get("ejemplo_optimizacion", "")

    with st.container(border=True):
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>Ana Lucia C. (Reclutadora Talento 360)</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("<h2>Tus resultados</h2>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='text-align: right;'><span style='font-size: 20px;'>Puntuación General</span><br><span style='font-size: 24px; font-weight: bold;'>{score} / 10</span></div>", unsafe_allow_html=True)
        
        st.markdown("<h4>Lo que hiciste genial</h4>", unsafe_allow_html=True)
        for p in fuertes:
            st.markdown(f"<li>{p}</li>", unsafe_allow_html=True)
            
        st.markdown("<h4 style='margin-top: 15px;'>Oportunidades para brillar más</h4>", unsafe_allow_html=True)
        for a in mejoras:
            st.markdown(f"<li>{a}</li>", unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center; margin-top: 30px;'>Ejemplo Práctico (Método STAR)</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Así podrías haber estructurado tu respuesta para generar mayor impacto:</p>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color: #666666; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>{ejemplo}</div>", unsafe_allow_html=True)

        if voice_on:
            if "eval_audio" not in st.session_state:
                full_text = (
                    f"Tus resultados están listos, {st.session_state.user_name}. Tu puntuación general es {score} sobre 10. "
                    f"En lo que hiciste genial destacamos: {', '.join(fuertes)}. "
                    f"Como oportunidades para brillar más te sugerimos: {', '.join(mejoras)}. "
                    f"Finalmente, aquí tienes un ejemplo aplicando el método estar: {ejemplo}"
                )
                st.session_state.eval_audio = text_to_speech(full_text)
            
            st.audio(st.session_state.eval_audio, format="audio/mp3")

    if st.button("Iniciar otra simulación"):
        restart()
        