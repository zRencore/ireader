"""
app.py
======
Aplicación Streamlit para la lectura de PDFs con voz.

Estilo visual: elegante y profesional, paleta ink-blue + copper/amber,
con soporte automático para modo claro/oscuro.
Soporta tres backends de TTS:
  - Edge-TTS (online, máxima calidad, recomendado)
  - Piper TTS (offline, calidad media)
  - pyttsx3 (offline, calidad baja, solo emergencia)

Dos modos de uso independientes:
  - Pestaña 1: Leer desde PDF (subir PDF → seleccionar páginas → editar → sintetizar)
  - Pestaña 2: Escribir texto directamente (escribir → sintetizar)

Cada pestaña tiene su propio panel de texto, botón de generar y reproductor.

Uso:
    streamlit run app.py
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components

from pdf_processor import (
    extract_pages_from_pdf,
    extract_full_text,
    get_document_stats,
    split_text_into_chunks,
)
import tts_engine


# ---------------------------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lector de PDF con Voz",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Estilos CSS: soporte modo claro/oscuro + barra lateral compacta
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap');

:root {
    --bg-app: #F6F5F1;
    --bg-app-alt: #EFEDE6;
    --bg-sidebar: #FBFAF7;
    --bg-card: #FFFFFF;
    --bg-card-hover: #F4F1E9;
    --bg-input: #FFFFFF;
    --border-color: #E3DFD3;
    --border-soft: #ECE9DF;
    --text-primary: #16192A;
    --text-secondary: #2E3348;
    --text-muted: #6D7185;
    --accent: #B5732E;
    --accent-hover: #9C5F23;
    --accent-soft: #FBF0E1;
    --accent-2: #1B2440;
    --badge-online-bg: #E7EEF7;
    --badge-online-text: #1F3A63;
    --badge-offline-bg: #E7F1E7;
    --badge-offline-text: #2E5B34;
    --badge-warning-bg: #FBEEDD;
    --badge-warning-text: #8A4E12;
    --uploader-border: #D9C9AE;
    --uploader-bg: #FBFAF7;
    --shadow-sm: 0 1px 2px 0 rgba(22,25,42,0.05);
    --shadow-md: 0 6px 16px -4px rgba(22,25,42,0.10), 0 2px 6px -2px rgba(22,25,42,0.06);
    --shadow-lg: 0 16px 32px -8px rgba(22,25,42,0.16), 0 4px 10px -4px rgba(22,25,42,0.08);
    --shadow-glow: 0 0 0 3px var(--accent-soft);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 18px;
    --gradient-accent: linear-gradient(135deg, #C6853F 0%, #A5652A 100%);
    --gradient-hero: linear-gradient(120deg, #1B2440 0%, #2E3457 55%, #B5732E 130%);
    --font-display: "Fraunces", "Georgia", serif;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-app: #0B0E19;
        --bg-app-alt: #0F1424;
        --bg-sidebar: #10152A;
        --bg-card: #141A30;
        --bg-card-hover: #1B2440;
        --bg-input: #0F1526;
        --border-color: #262F4D;
        --border-soft: #1B2138;
        --text-primary: #F1EEE6;
        --text-secondary: #D6D6E4;
        --text-muted: #8B90A8;
        --accent: #DB9A54;
        --accent-hover: #EBB278;
        --accent-soft: rgba(219,154,84,0.14);
        --accent-2: #E8AD70;
        --badge-online-bg: #1B2C4D;
        --badge-online-text: #A9C7EE;
        --badge-offline-bg: #163521;
        --badge-offline-text: #9BDCAE;
        --badge-warning-bg: #3A2711;
        --badge-warning-text: #EFC088;
        --uploader-border: #3A3355;
        --uploader-bg: #141A30;
        --shadow-sm: 0 1px 2px 0 rgba(0,0,0,0.35);
        --shadow-md: 0 8px 20px -6px rgba(0,0,0,0.55), 0 2px 8px -2px rgba(0,0,0,0.4);
        --shadow-lg: 0 20px 40px -10px rgba(0,0,0,0.65), 0 6px 14px -6px rgba(0,0,0,0.45);
        --shadow-glow: 0 0 0 3px var(--accent-soft);
        --gradient-accent: linear-gradient(135deg, #E8AD70 0%, #C17F3E 100%);
        --gradient-hero: linear-gradient(120deg, #0B0E19 0%, #1B2440 55%, #B5732E 160%);
    }
}

* { scrollbar-width: thin; scrollbar-color: var(--border-color) transparent; }

.stApp {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg-app);
    background-image:
        radial-gradient(circle at 15% 0%, rgba(181,115,46,0.06), transparent 45%),
        radial-gradient(circle at 85% 100%, rgba(27,36,64,0.05), transparent 40%);
    color: var(--text-secondary);
}

/* === Tipografía === */
h1 {
    font-family: var(--font-display);
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    color: var(--text-primary) !important;
    font-size: 2rem !important;
}
h2, h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em;
}
h3 { font-size: 1.05rem !important; }

/* === Header nativo de Streamlit: aquí se inyecta el icono + nombre + descripción === */
header[data-testid="stHeader"] {
    height: auto !important;
    min-height: 4.1rem !important;
    background: var(--gradient-hero) !important;
    box-shadow: var(--shadow-lg) !important;
    align-items: center !important;
}
header[data-testid="stHeader"] > div {
    align-items: center !important;
}
#injected-app-hero {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    display: flex;
    align-items: center;
    gap: 0.65rem;
    max-width: 58%;
    pointer-events: none;
}
#injected-app-hero .app-hero-icon {
    flex-shrink: 0;
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    border-radius: 11px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.20);
}
#injected-app-hero .app-hero-text h1 {
    font-family: var(--font-display) !important;
    color: #FBFAF7 !important;
    margin: 0 !important;
    font-size: 1.05rem !important;
    line-height: 1.2 !important;
}
#injected-app-hero .app-hero-text p {
    margin: 0.1rem 0 0 0;
    color: rgba(251,250,247,0.75);
    font-size: 0.72rem;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
/* El bloque de componentes de Streamlit que dispara la inyección no debe ocupar espacio */
div[data-testid="stIFrame"][title="app_hero_injector"],
iframe[title="app_hero_injector"] {
    display: none !important;
}

/* === Botones === */
.stButton > button {
    background: var(--gradient-accent);
    color: #FFF7EE !important;
    border: none;
    padding: 0.55rem 1.15rem;
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.88rem;
    letter-spacing: 0.01em;
    transition: all 0.2s cubic-bezier(.2,.7,.3,1);
    box-shadow: var(--shadow-sm);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
    filter: brightness(1.05);
}
.stButton > button:active {
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
}
.stButton > button:focus-visible {
    outline: none;
    box-shadow: var(--shadow-glow);
}
.stButton > button:disabled {
    background: var(--bg-card-hover);
    color: var(--text-muted) !important;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
    opacity: 0.7;
}
.stButton > button[kind="secondary"] {
    background: var(--bg-card);
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
}
.stButton > button[kind="secondary"]:hover {
    background-color: var(--bg-card-hover);
    border-color: var(--accent);
    color: var(--accent) !important;
    filter: none;
}

/* === Barra lateral: encaja exactamente en la altura de la pantalla === */
section[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar);
    border-right: 1px solid var(--border-color);
    height: 100vh !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] > div {
    height: 100vh !important;
}
/* Contenedor scrolleable interno de Streamlit: lo convertimos en columna flex
   para que su contenido se reparta en TODA la altura disponible */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] .block-container {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100% !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
}
/* La columna de widgets ocupa el 100% de la altura; el espacio libre se
   reparte automáticamente entre los separadores (ver regla ":has(hr)" abajo) */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    gap: 0.4rem !important;
}
section[data-testid="stSidebar"] .element-container {
    flex: 0 0 auto !important;
    margin-bottom: 0 !important;
}
/* Cada separador "---" actúa como espaciador flexible: absorbe todo el
   espacio sobrante para que el contenido llene exactamente el alto de
   pantalla, sin huecos arriba ni abajo */
section[data-testid="stSidebar"] .element-container:has(hr) {
    flex: 1 1 auto !important;
    display: flex !important;
    align-items: center !important;
    min-height: 0.6rem;
}
section[data-testid="stSidebar"] h2 {
    margin-top: 0 !important;
    margin-bottom: 0.4rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid var(--border-soft);
}
section[data-testid="stSidebar"] h3 {
    margin-top: 0 !important;
    margin-bottom: 0.15rem !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent) !important;
    opacity: 0.95;
}
section[data-testid="stSidebar"] hr {
    margin: 0 !important;
    border-color: var(--border-soft) !important;
    width: 100%;
}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    margin-top: 0.05rem !important;
    margin-bottom: 0 !important;
    line-height: 1.3 !important;
    font-size: 0.76rem !important;
}
section[data-testid="stSidebar"] .stSlider {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}
section[data-testid="stSidebar"] .stSlider > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
    height: 20px !important;
}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div:nth-child(2) {
    margin-bottom: 0 !important;
}
.stSlider [data-baseweb="slider"] [role="slider"] {
    background-color: var(--accent) !important;
    border: 2px solid var(--bg-card) !important;
    box-shadow: var(--shadow-sm) !important;
}
section[data-testid="stSidebar"] .param-label {
    margin-top: 0 !important;
    font-size: 0.8rem !important;
}
section[data-testid="stSidebar"] .stSelectbox {
    margin-bottom: 0 !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    border-radius: var(--radius-sm) !important;
    border-color: var(--border-color) !important;
    background-color: var(--bg-input) !important;
    min-height: 34px !important;
}
section[data-testid="stSidebar"] .stSelectbox label {
    margin-bottom: 0.05rem !important;
    font-size: 0.8rem !important;
    font-weight: 500;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background-color: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
}
/* Compactar badges y textos pequeños de la sidebar (país/voz activa, etc.) */
section[data-testid="stSidebar"] .stMarkdown p {
    margin-bottom: 0 !important;
    font-size: 0.8rem !important;
}

/* === Métricas (cards modernos) === */
[data-testid="stMetric"] {
    background-color: var(--bg-card);
    padding: 0.9rem 1.05rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-soft);
    box-shadow: var(--shadow-sm);
    transition: all 0.22s cubic-bezier(.2,.7,.3,1);
}
[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--accent);
}
[data-testid="stMetricValue"] {
    color: var(--accent) !important;
    font-weight: 700 !important;
    font-size: 1.35rem !important;
    font-family: var(--font-display);
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.76rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600 !important;
}

/* === Sliders globales === */
.stSlider > div > div > div > div {
    background: var(--gradient-accent) !important;
}

/* === Selectboxes globales === */
.stSelectbox > div > div {
    border-radius: var(--radius-sm) !important;
    border-color: var(--border-color) !important;
    background-color: var(--bg-input) !important;
    color: var(--text-primary) !important;
    transition: border-color 0.18s ease;
}
.stSelectbox > div > div:hover {
    border-color: var(--accent) !important;
}

/* === Inputs y text areas === */
input, textarea {
    background-color: var(--bg-input) !important;
    color: var(--text-primary) !important;
}
textarea {
    border-radius: var(--radius-md) !important;
    border-color: var(--border-color) !important;
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 "Helvetica Neue", Arial, sans-serif !important;
    line-height: 1.6 !important;
    box-shadow: var(--shadow-sm) inset;
}
textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* === File uploader === */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--uploader-border) !important;
    border-radius: var(--radius-md) !important;
    background-color: var(--uploader-bg) !important;
    padding: 1.1rem !important;
    transition: all 0.22s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
    background-color: var(--accent-soft) !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: var(--gradient-accent) !important;
    color: #FFF7EE !important;
    border: none !important;
}

/* === Alertas === */
.stAlert > div {
    border-radius: var(--radius-md) !important;
    border: none !important;
    box-shadow: var(--shadow-sm);
}
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentSuccess"],
[data-testid="stAlertContentWarning"], [data-testid="stAlertContentError"] {
    border-left: 3px solid currentColor;
    padding-left: 0.6rem;
}

/* === Reproductor de audio === */
audio {
    width: 100% !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm);
}

/* === Contenedor principal === */
.block-container {
    padding-top: 5.2rem !important;
    padding-bottom: 1.2rem !important;
    max-width: 1120px;
}

/* === Divisores === */
hr {
    border-color: var(--border-soft) !important;
    margin: 0.6rem 0 !important;
    border-top-width: 1px;
}

/* === Encabezados de contenido más compactos === */
.main h3 {
    margin-top: 0.3rem !important;
    margin-bottom: 0.3rem !important;
}
.main .stTabs {
    margin-top: -0.3rem;
}
.main [data-testid="stCaptionContainer"] {
    margin-bottom: 0.2rem !important;
}
.main [data-testid="stMarkdownContainer"] > p {
    margin-bottom: 0.3rem !important;
}

/* === Captions === */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    line-height: 1.45 !important;
}

/* === Badges === */
.backend-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-left: 4px;
    text-transform: uppercase;
}
.badge-online {
    background-color: var(--badge-online-bg);
    color: var(--badge-online-text);
}
.badge-offline {
    background-color: var(--badge-offline-bg);
    color: var(--badge-offline-text);
}
.badge-warning {
    background-color: var(--badge-warning-bg);
    color: var(--badge-warning-text);
}

/* === Tabs modernos === */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.3rem;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 1.2rem;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.6rem 1.2rem;
    background-color: transparent;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    color: var(--text-muted) !important;
    font-weight: 600;
    font-size: 0.92rem;
    border-bottom: 2px solid transparent;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background-color: var(--bg-card);
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    background-color: transparent !important;
    border-bottom: 2px solid var(--accent) !important;
    font-weight: 700;
}

/* === Etiquetas de parámetros en sidebar === */
.param-label {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.85rem;
    margin-top: 0.35rem;
    margin-bottom: 0;
    display: block;
    letter-spacing: -0.005em;
}

/* === File uploader compacto en sidebar === */
section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    padding: 0.5rem !important;
}

/* === Sección de tarjeta suave para agrupar contenido === */
.soft-section {
    background-color: var(--bg-card);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    margin: 0.75rem 0 1.1rem 0;
}

/* === Animaciones sutiles === */
.stButton, .stMetric, [data-testid="stFileUploader"] {
    transition: all 0.2s ease;
}

/* === Progreso === */
.stProgress > div > div > div > div {
    background: var(--gradient-accent) !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Estado de la sesión
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    defaults = {
        "pdf_pages": [],
        "pdf_filename": None,
        "selected_voice": None,
        "selected_backend": None,
        # Audio separado por pestaña para que no se mezclen
        "pdf_audio_bytes": None,
        "pdf_audio_format": "audio/wav",
        "direct_audio_bytes": None,
        "direct_audio_format": "audio/wav",
        # Portapapeles virtual (para copiar/pegar entre sesiones o desde fuera)
        "_clipboard": "",
        # Mensajes de feedback para los botones copiar/pegar/limpiar
        "_pdf_feedback": "",
        "_direct_feedback": "",
        # Flags de acciones pendientes (se procesan al inicio del siguiente render
        # ANTES de instanciar los widgets, evitando el error de Streamlit
        # "session_state cannot be modified after widget is instantiated")
        "_pending_text_action": None,  # tuple (text_area_key, action, payload)
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


def _schedule_text_action(text_area_key: str, action: str, payload: str = "") -> None:
    """
    Programa una acción sobre un text_area para ejecutarla en el SIGUIENTE render,
    ANTES de que el widget se instancie. Esto evita el error:
    "st.session_state.X cannot be modified after the widget with key X is instantiated".

    Acciones soportadas:
    - "paste": reemplaza el contenido del panel con payload
    - "clear": vacía el panel
    - "import": reemplaza el contenido del panel con payload (texto importado de .txt)
    """
    st.session_state["_pending_text_action"] = (text_area_key, action, payload)


def _process_pending_text_action() -> None:
    """
    Procesa la acción pendiente al inicio del render, antes de instanciar widgets.
    Debe llamarse al principio del cuerpo principal de la app.
    """
    pending = st.session_state.get("_pending_text_action")
    if pending is None:
        return

    text_area_key, action, payload = pending
    # Limpiar el flag inmediatamente para no procesarlo dos veces
    st.session_state["_pending_text_action"] = None

    if action in ("paste", "import"):
        st.session_state[text_area_key] = payload
    elif action == "clear":
        st.session_state[text_area_key] = ""


# Procesar acciones pendientes ANTES de instanciar cualquier widget.
# Esto debe ejecutarse al inicio de cada render, después de init_session_state
# pero antes de cualquier st.text_area, st.button, etc.
_process_pending_text_action()


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_pyttsx3_voices_cached() -> List[Dict[str, str]]:
    """Lista las voces pyttsx3 disponibles y cachea el resultado 1 hora."""
    return tts_engine.list_pyttsx3_voices()


def filter_voices_by_country(
    voices_dict: Dict[str, Dict[str, str]], country: str
) -> List[str]:
    """Filtra voces Edge por país. Si country == 'Todos', devuelve todas."""
    if country == "Todos":
        return list(voices_dict.keys())
    return [
        name for name, info in voices_dict.items()
        if info["country"] == country
    ]


def param_label(text: str) -> None:
    """Renderiza una etiqueta de parámetro con estilo compacto."""
    st.markdown(f"<span class='param-label'>{text}</span>", unsafe_allow_html=True)


def render_text_actions(
    text_area_key: str,
    feedback_key: str,
    copy_button_key: str,
    paste_button_key: str,
    clear_button_key: str,
) -> str:
    """
    Renderiza una fila con 3 botones: Copiar, Pegar y Limpiar.

    Devuelve el texto actual del panel.

    IMPORTANTE: Para modificar el contenido del text_area usamos el patrón de
    "acción pendiente" (_schedule_text_action) que se procesa al inicio del
    SIGUIENTE render, antes de que el widget se instancie. Esto evita el error:
    "st.session_state.X cannot be modified after the widget with key X is
    instantiated".

    - **Copiar**: copia el contenido actual del panel al portapapeles del
      sistema mediante JavaScript y al portapapeles virtual interno.
    - **Pegar**: pega el contenido del portapapeles virtual interno en el panel.
    - **Limpiar**: vacía completamente el panel.
    """
    current_text = st.session_state.get(text_area_key, "")

    # Fila de 3 botones distribuidos uniformemente
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Copiar", key=copy_button_key, use_container_width=True):
            if current_text.strip():
                # Guardar en portapapeles virtual interno
                st.session_state["_clipboard"] = current_text
                # Intentar copiar al portapapeles del sistema vía JavaScript
                escaped = (
                    current_text
                    .replace("\\", "\\\\")
                    .replace("'", "\\'")
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                )
                js_code = f"""
                <script>
                (function() {{
                    const text = '{escaped}';
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        navigator.clipboard.writeText(text).then(function() {{
                            console.log('Texto copiado al portapapeles');
                        }}).catch(function(err) {{
                            console.warn('No se pudo copiar al portapapeles:', err);
                            const ta = document.createElement('textarea');
                            ta.value = text;
                            document.body.appendChild(ta);
                            ta.select();
                            try {{ document.execCommand('copy'); }} catch(e) {{}}
                            document.body.removeChild(ta);
                        }});
                    }} else {{
                        const ta = document.createElement('textarea');
                        ta.value = text;
                        document.body.appendChild(ta);
                        ta.select();
                        try {{ document.execCommand('copy'); }} catch(e) {{}}
                        document.body.removeChild(ta);
                    }}
                }})();
                </script>
                """
                st.components.v1.html(js_code, height=0)
                st.session_state[feedback_key] = (
                    f"✅ Copiado: {len(current_text):,} caracteres al portapapeles."
                )
            else:
                st.session_state[feedback_key] = "ℹ️ No hay texto para copiar."

    with col2:
        if st.button("📥 Pegar", key=paste_button_key, use_container_width=True):
            clipboard_content = st.session_state.get("_clipboard", "")
            if clipboard_content:
                # Programar la acción para el próximo render (evita el error
                # de "widget already instantiated")
                _schedule_text_action(text_area_key, "paste", clipboard_content)
                st.session_state[feedback_key] = (
                    f"✅ Pegado desde portapapeles interno: {len(clipboard_content):,} caracteres."
                )
                st.rerun()
            else:
                st.session_state[feedback_key] = (
                    "ℹ️ El portapapeles interno está vacío. "
                    "Para pegar texto externo, haz clic en el panel y usa Ctrl+V."
                )

    with col3:
        if st.button("🗑️ Limpiar", key=clear_button_key, use_container_width=True):
            if current_text.strip():
                # Programar la limpieza para el próximo render
                _schedule_text_action(text_area_key, "clear", "")
                st.session_state[feedback_key] = "✅ Panel limpiado."
                st.rerun()
            else:
                st.session_state[feedback_key] = "ℹ️ El panel ya está vacío."

    # Mostrar mensaje de feedback si existe
    feedback = st.session_state.get(feedback_key, "")
    if feedback:
        st.caption(feedback)

    # Devolver el texto actual (no el modificado, que se verá en el próximo render)
    return st.session_state.get(text_area_key, "")


def run_synthesis(
    text: str,
    audio_key_prefix: str,
    backend: str,
    voice: str,
    # Edge-TTS params
    rate_percent: int = 0,
    pitch_hz: int = 0,
    volume_percent: int = 0,
    # Piper params
    length_scale: float = 1.0,
    noise_scale: float = 0.0,
    pitch_shift: float = 0.0,
    # pyttsx3 params
    speed_pyttsx: int = 0,
) -> None:
    """
    Ejecuta la síntesis de voz completa y guarda el resultado en
    session_state[audio_key_prefix + "_bytes"] y session_state[audio_key_prefix + "_format"].

    Muestra barra de progreso y mensajes de éxito/error.
    """
    chunks = split_text_into_chunks(text, max_chars=500)

    if not chunks:
        st.warning("No hay texto para sintetizar.")
        return

    progress = st.progress(0, "Preparando síntesis...")
    total_chunks = len(chunks)
    error_count = 0

    # =================================================================
    # CASO EDGE-TTS (produce MP3)
    # =================================================================
    if "Edge-TTS" in backend:
        mp3_chunks: List[bytes] = []
        voice_id = tts_engine.EDGE_VOICES[voice]["voice_id"]

        for i, chunk in enumerate(chunks):
            pct = int((i / total_chunks) * 100)
            progress.progress(
                pct,
                f"Sintetizando fragmento {i + 1} de {total_chunks} con Edge-TTS...",
            )
            try:
                mp3_data = tts_engine.synthesize_with_edge(
                    text=chunk,
                    voice_id=voice_id,
                    rate_percent=rate_percent,
                    pitch_hz=pitch_hz,
                    volume_percent=volume_percent,
                )
                if mp3_data:
                    mp3_chunks.append(mp3_data)
                else:
                    error_count += 1
            except Exception as exc:
                error_count += 1
                st.warning(f"Error en fragmento {i + 1}: {exc}")

        if mp3_chunks:
            progress.progress(95, "Concatenando audio MP3...")
            final_mp3 = tts_engine.concatenate_mp3_chunks(mp3_chunks)
            st.session_state[audio_key_prefix + "_bytes"] = final_mp3
            st.session_state[audio_key_prefix + "_format"] = "audio/mp3"
            progress.progress(100, "✅ Audio listo")
            msg = "Audio generado correctamente con Edge-TTS."
            if error_count > 0:
                msg += f" ⚠️ {error_count} fragmento(s) con error (de {total_chunks})."
            st.success(msg)
            progress.empty()
        else:
            progress.empty()
            st.error(
                "❌ No se pudo generar audio. Posibles causas:\n"
                "- No tienes conexión a internet\n"
                "- Firewall o proxy bloquea servidores Microsoft\n\n"
                "Prueba cambiando al backend **Piper TTS** (offline)."
            )

    # =================================================================
    # CASO PIPER (produce WAV)
    # =================================================================
    elif "Piper" in backend:
        audio_segments: List = []

        for i, chunk in enumerate(chunks):
            pct = int((i / total_chunks) * 100)
            progress.progress(
                pct,
                f"Sintetizando fragmento {i + 1} de {total_chunks} con Piper...",
            )
            try:
                sr, audio = tts_engine.synthesize_with_piper(
                    text=chunk,
                    voice_name=voice,
                    length_scale=length_scale,
                    noise_scale=noise_scale,
                    pitch_shift=pitch_shift,
                )
                if len(audio) > 0:
                    audio_segments.append((sr, audio))
                else:
                    error_count += 1
            except Exception as exc:
                error_count += 1
                st.warning(f"Error en fragmento {i + 1}: {exc}")

        if audio_segments:
            progress.progress(95, "Concatenando audio WAV...")
            final_sr, final_audio = tts_engine.concatenate_audio(audio_segments)
            wav_bytes = tts_engine.audio_to_wav_bytes(final_sr, final_audio)
            st.session_state[audio_key_prefix + "_bytes"] = wav_bytes
            st.session_state[audio_key_prefix + "_format"] = "audio/wav"
            progress.progress(100, "✅ Audio listo")
            msg = "Audio generado correctamente con Piper."
            if error_count > 0:
                msg += f" ⚠️ {error_count} fragmento(s) con error (de {total_chunks})."
            st.success(msg)
            progress.empty()
        else:
            progress.empty()
            st.error("❌ No se pudo generar audio con Piper.")

    # =================================================================
    # CASO PYTTSX3
    # =================================================================
    else:
        audio_segments: List = []

        for i, chunk in enumerate(chunks):
            pct = int((i / total_chunks) * 100)
            progress.progress(
                pct,
                f"Sintetizando fragmento {i + 1} de {total_chunks} con pyttsx3...",
            )
            try:
                sr, audio = tts_engine.synthesize_with_pyttsx3(
                    text=chunk,
                    voice_id=voice,
                    rate=speed_pyttsx,
                )
                if len(audio) > 0:
                    audio_segments.append((sr, audio))
                else:
                    error_count += 1
            except Exception as exc:
                error_count += 1
                st.warning(f"Error en fragmento {i + 1}: {exc}")

        if audio_segments:
            progress.progress(95, "Concatenando audio WAV...")
            final_sr, final_audio = tts_engine.concatenate_audio(audio_segments)
            wav_bytes = tts_engine.audio_to_wav_bytes(final_sr, final_audio)
            st.session_state[audio_key_prefix + "_bytes"] = wav_bytes
            st.session_state[audio_key_prefix + "_format"] = "audio/wav"
            progress.progress(100, "✅ Audio listo")
            msg = "Audio generado correctamente."
            if error_count > 0:
                msg += f" ⚠️ {error_count} fragmento(s) con error (de {total_chunks})."
            st.success(msg)
            progress.empty()
        else:
            progress.empty()
            st.error("❌ No se pudo generar audio con pyttsx3.")


def render_player(audio_key_prefix: str, download_filename: str) -> None:
    """Renderiza el reproductor y botón de descarga si hay audio generado."""
    audio_bytes = st.session_state.get(audio_key_prefix + "_bytes")
    if audio_bytes:
        st.markdown("---")
        st.markdown("### ▶️ Reproductor")
        audio_fmt = st.session_state.get(audio_key_prefix + "_format", "audio/wav")
        file_ext = "mp3" if "mp3" in audio_fmt else "wav"
        st.audio(audio_bytes, format=audio_fmt)
        st.download_button(
            label=f"💾 Descargar audio (.{file_ext.upper()})",
            data=audio_bytes,
            file_name=download_filename + f".{file_ext}",
            mime=audio_fmt,
            use_container_width=True,
        )


# ===========================================================================
# BARRA LATERAL: configuración de voz y motor TTS (COMPACTA)
# ===========================================================================
with st.sidebar:
    st.markdown("## ⚙️ Configuración")

    backends = tts_engine.list_available_backends()
    if not backends:
        st.error(
            "No se detectó ningún motor TTS instalado. "
            "Instala las dependencias con `pip install -r requirements.txt`."
        )
        st.stop()

    default_idx = 0
    for i, b in enumerate(backends):
        if "Edge-TTS" in b:
            default_idx = i
            break

    selected_backend = st.selectbox(
        "Motor de voz",
        options=backends,
        index=default_idx,
        help="Edge-TTS ofrece la mejor calidad (requiere internet). "
             "Piper y pyttsx3 funcionan offline.",
    )
    st.session_state["selected_backend"] = selected_backend

    if "Edge-TTS" in selected_backend:
        st.markdown(
            "🌐 <span class='backend-badge badge-online'>Online</span> "
            "<small style='color: var(--text-muted)'>Alta calidad · Internet</small>",
            unsafe_allow_html=True,
        )
    elif "Piper" in selected_backend:
        st.markdown(
            "🔒 <span class='backend-badge badge-offline'>Offline</span> "
            "<small style='color: var(--text-muted)'>Calidad media · Sin internet</small>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "⚠️ <span class='backend-badge badge-warning'>Offline</span> "
            "<small style='color: var(--text-muted)'>Baja calidad · Emergencia</small>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Variables de ajustes (se sobreescriben según el backend)
    rate_percent = 0
    pitch_hz = 0
    volume_percent = 0
    length_scale = 1.0
    noise_scale = 0.0
    pitch_shift = 0.0
    speed_pyttsx = 0

    # =====================================================================
    # CONFIGURACIÓN EDGE-TTS
    # =====================================================================
    if "Edge-TTS" in selected_backend:
        st.markdown("### 🎙️ Voz Edge-TTS")

        # País y Voz en filas separadas (no en columnas) para mejor legibilidad
        countries = sorted(set(v["country"] for v in tts_engine.EDGE_VOICES.values()))
        selected_country = st.selectbox(
            "País",
            options=["Todos"] + countries,
            help="Filtra las voces por país."
        )
        filtered_voices = filter_voices_by_country(
            tts_engine.EDGE_VOICES, selected_country
        )
        selected_voice = st.selectbox(
            "Voz",
            options=filtered_voices,
            index=0,
            help=f"{len(filtered_voices)} voces disponibles.",
        )
        st.session_state["selected_voice"] = selected_voice

        voice_info = tts_engine.EDGE_VOICES[selected_voice]
        st.caption(
            f"{voice_info['gender'].capitalize()} · {voice_info['country']} · "
            f"`{voice_info['voice_id']}`"
        )

        st.markdown("---")
        st.markdown("### 🎛️ Ajustes de voz")

        param_label("Velocidad")
        rate_percent = st.slider(
            "Velocidad (%)",
            min_value=-50, max_value=100, value=0, step=5,
            help="0 = normal. +50 = 50% más rápido. -50 = 50% más lento.",
            label_visibility="collapsed",
        )

        param_label("Tono")
        pitch_hz = st.slider(
            "Tono (Hz)",
            min_value=-20, max_value=20, value=0, step=1,
            help="0 = original. Positivo = más agudo. Negativo = más grave.",
            label_visibility="collapsed",
        )

        param_label("Volumen")
        volume_percent = st.slider(
            "Volumen (%)",
            min_value=-50, max_value=50, value=0, step=5,
            help="0 = normal. Positivo = más alto.",
            label_visibility="collapsed",
        )

    # =====================================================================
    # CONFIGURACIÓN PIPER
    # =====================================================================
    elif "Piper" in selected_backend:
        st.markdown("### 🎙️ Voces Piper (español)")

        voice_options = list(tts_engine.PIPER_VOICES.keys())
        selected_voice = st.selectbox(
            "Voz",
            options=voice_options,
            help="Voces neuronales gratuitas en español (offline).",
        )
        st.session_state["selected_voice"] = selected_voice

        voice_info = tts_engine.PIPER_VOICES[selected_voice]
        st.caption(f"Género: **{voice_info['gender']}**")

        if not tts_engine.is_voice_downloaded(selected_voice):
            st.warning("Voz no descargada.")
            if st.button("⬇️ Descargar (~60 MB)", use_container_width=True):
                progress_bar = st.progress(0, "Iniciando descarga...")
                success, message = tts_engine.download_piper_voice(
                    selected_voice,
                    progress_callback=lambda p, m: progress_bar.progress(p, m),
                )
                if success:
                    progress_bar.progress(100, "✅ Descarga completa")
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
                    progress_bar.empty()
        else:
            st.success("✅ Voz disponible localmente")

        st.markdown("---")
        st.markdown("### 🎛️ Ajustes de voz")

        param_label("Velocidad")
        speed = st.slider(
            "Velocidad",
            min_value=0.5, max_value=2.0, value=1.0, step=0.05,
            help="1.0 = velocidad normal.",
            label_visibility="collapsed",
        )
        length_scale = 1.0 / speed

        param_label("Tono")
        pitch_shift = st.slider(
            "Tono (semitonos)",
            min_value=-6.0, max_value=6.0, value=0.0, step=0.5,
            help="0 = original. Positivo = más agudo.",
            label_visibility="collapsed",
        )

        param_label("Expresividad")
        noise_scale = st.slider(
            "Expresividad",
            min_value=0.0, max_value=1.0, value=0.667, step=0.05,
            help="Mayor = entonación más variada.",
            label_visibility="collapsed",
        )

    # =====================================================================
    # CONFIGURACIÓN PYTTSX3
    # =====================================================================
    else:
        st.markdown("### 🎙️ Voces Windows (SAPI5)")

        sapi_voices = get_pyttsx3_voices_cached()
        if sapi_voices:
            voice_names = [v["name"] for v in sapi_voices]
            selected_idx = st.selectbox(
                "Voz",
                options=range(len(voice_names)),
                format_func=lambda i: voice_names[i],
            )
            st.session_state["selected_voice"] = sapi_voices[selected_idx]["id"]
            st.caption(f"Voz: {voice_names[selected_idx]}")
        else:
            st.info(
                "No se detectaron voces en español. "
                "Se usará la voz por defecto del sistema."
            )
            st.session_state["selected_voice"] = None

        st.markdown("---")
        st.markdown("### 🎛️ Ajustes de voz")

        param_label("Velocidad")
        speed_pyttsx = st.slider(
            "Velocidad",
            min_value=-50, max_value=100, value=0, step=10,
            help="0 = normal. Positivo = más rápido.",
            label_visibility="collapsed",
        )

    st.markdown("---")
    st.caption(
        "🔒 Edge-TTS envía texto a Microsoft. Piper/pyttsx3 funcionan offline."
    )


# ===========================================================================
# CONTENIDO PRINCIPAL
# ===========================================================================
# El icono + nombre + descripción se inyectan directamente dentro del header
# nativo de Streamlit (donde vive el botón "Deploy"), NO en el área de contenido.
components.html(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        const header = doc.querySelector('header[data-testid="stHeader"]');
        if (!header) { return; }

        const prev = header.querySelector('#injected-app-hero');
        if (prev) { prev.remove(); }

        const hero = doc.createElement('div');
        hero.id = 'injected-app-hero';
        hero.innerHTML = `
            <div class="app-hero-icon">📚</div>
            <div class="app-hero-text">
                <h1>Lector de PDF con Voz</h1>
                <p>Lee PDFs digitales en español o ingresa texto directamente para
                sintetizar a voz, con Edge-TTS, Piper o pyttsx3.</p>
            </div>
        `;
        header.style.position = header.style.position || 'fixed';
        header.appendChild(hero);
    })();
    </script>
    """,
    height=0,
)


# Variables compartidas para la síntesis (definidas en la barra lateral)
backend = st.session_state["selected_backend"]
voice = st.session_state["selected_voice"]

# Determinar si la voz está disponible para generar
def voice_is_ready(backend: str, voice: Optional[str]) -> bool:
    """Verifica si el backend y la voz están listos para sintetizar."""
    if "Edge-TTS" in backend:
        return True  # Edge-TTS no requiere descarga
    if "Piper" in backend:
        return bool(voice) and tts_engine.is_voice_downloaded(voice)
    return True  # pyttsx3 siempre disponible


# ===========================================================================
# PESTAÑAS
# ===========================================================================
tab_pdf, tab_direct = st.tabs([
    "📄 Leer desde PDF",
    "✏️ Escribir texto directamente",
])


# ===========================================================================
# PESTAÑA 1: Leer desde PDF
# ===========================================================================
with tab_pdf:
    uploaded_file = st.file_uploader(
        "Arrastra tu PDF aquí o haz clic para seleccionar",
        type=["pdf"],
        help="Solo se admiten PDFs digitales (con texto seleccionable).",
    )

    if uploaded_file is not None:
        # Procesar PDF solo si es nuevo o cambió
        if st.session_state["pdf_filename"] != uploaded_file.name:
            with st.spinner("Extrayendo texto del PDF..."):
                pdf_bytes = uploaded_file.getvalue()
                try:
                    pages = extract_pages_from_pdf(pdf_bytes)
                    if not pages:
                        st.error("El PDF está vacío o no se pudo leer.")
                        pages = []
                    st.session_state["pdf_pages"] = pages
                    st.session_state["pdf_filename"] = uploaded_file.name
                    st.session_state["pdf_audio_bytes"] = None  # limpiar audio previo
                except Exception as exc:
                    st.error(f"No se pudo procesar el PDF: {exc}")
                    pages = []
                    st.session_state["pdf_pages"] = []
                    st.session_state["pdf_filename"] = uploaded_file.name

        pdf_pages = st.session_state.get("pdf_pages", [])
        stats = get_document_stats(pdf_pages) if pdf_pages else None

        if stats and stats["total_pages"] > 0:
            # Métricas del documento
            st.markdown("### 📊 Información del documento")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Páginas", stats["total_pages"])
            with col2:
                st.metric("Páginas con texto", stats["pages_with_text"])
            with col3:
                st.metric("Palabras", f"{stats['total_words']:,}")
            with col4:
                st.metric("Duración aprox.", f"{stats['estimated_minutes']} min")

            # Aviso si el PDF parece escaneado
            if stats["pages_with_text"] == 0:
                st.error(
                    "⚠️ **No se detectó texto seleccionable en el PDF.** "
                    "Probablemente sea una imagen escaneada. Esta versión no soporta OCR."
                )
            else:
                if stats["pages_with_text"] < stats["total_pages"]:
                    st.info(
                        f"ℹ️ {stats['total_pages'] - stats['pages_with_text']} página(s) "
                        f"sin texto extraíble (probablemente imágenes)."
                    )

                st.markdown("---")
                st.markdown("### 📖 Selecciona el rango de páginas")
                col_start, col_end = st.columns(2)
                with col_start:
                    start_page = st.number_input(
                        "Página inicial",
                        min_value=1,
                        max_value=stats["total_pages"],
                        value=1,
                        step=1,
                    )
                with col_end:
                    end_page = st.number_input(
                        "Página final",
                        min_value=min(start_page, stats["total_pages"]),
                        max_value=stats["total_pages"],
                        value=stats["total_pages"],
                        step=1,
                    )

                selected_pages = pdf_pages[start_page - 1 : end_page]
                extracted_text = extract_full_text(selected_pages)

                if extracted_text.strip():
                    # --- Panel de texto editable ---
                    st.markdown("---")
                    st.markdown("### 📝 Texto extraído (editable)")
                    st.caption(
                        "✏️ Puedes editar este texto antes de generar el audio. "
                        "Se sintetizará exactamente lo que veas aquí, ideal para eliminar "
                        "encabezados repetidos, números de página o corregir errores."
                    )

                    # Clave única ligada al rango de páginas y al PDF:
                    # si el usuario cambia el rango o el PDF, se reinicia el contenido.
                    text_area_key = f"pdf_text_{st.session_state['pdf_filename']}_{start_page}_{end_page}"

                    last_key = st.session_state.get("_last_pdf_text_key")
                    if last_key != text_area_key:
                        st.session_state[text_area_key] = extracted_text
                        st.session_state["_last_pdf_text_key"] = text_area_key

                    edited_text = st.text_area(
                        "Texto a leer",
                        key=text_area_key,
                        height=220,
                        label_visibility="collapsed",
                    )

                    # Contador
                    char_count = len(edited_text)
                    word_count = len(edited_text.split()) if edited_text.strip() else 0
                    st.caption(f"📊 {char_count:,} caracteres · {word_count:,} palabras")

                    # --- Botones de copiar/pegar/limpiar ---
                    edited_text = render_text_actions(
                        text_area_key=text_area_key,
                        feedback_key="_pdf_feedback",
                        copy_button_key="btn_copy_pdf",
                        paste_button_key="btn_paste_pdf",
                        clear_button_key="btn_clear_pdf",
                    )

                    # --- Generación de audio ---
                    st.markdown("---")
                    st.markdown("### 🔊 Generar audio")

                    can_generate = bool(edited_text.strip()) and voice_is_ready(backend, voice)

                    if not voice_is_ready(backend, voice):
                        st.info("ℹ️ Descarga la voz Piper en la barra lateral primero.")

                    if st.button(
                        "🎙️ Generar audio",
                        disabled=not can_generate,
                        use_container_width=True,
                        type="primary",
                        key="btn_generate_pdf",
                    ):
                        run_synthesis(
                            text=edited_text,
                            audio_key_prefix="pdf",
                            backend=backend,
                            voice=voice,
                            rate_percent=rate_percent,
                            pitch_hz=pitch_hz,
                            volume_percent=volume_percent,
                            length_scale=length_scale,
                            noise_scale=noise_scale,
                            pitch_shift=pitch_shift,
                            speed_pyttsx=speed_pyttsx,
                        )

                    # --- Reproductor ---
                    download_name = st.session_state.get("pdf_filename", "audio") or "audio"
                    render_player("pdf", download_name)
                else:
                    st.warning(
                        "No se pudo extraer texto de las páginas seleccionadas. "
                        "Es posible que estas páginas contengan solo imágenes o diagramas."
                    )
    else:
        # Estado inicial de la pestaña PDF
        st.info("👆 Sube un PDF digital para comenzar.")


# ===========================================================================
# PESTAÑA 2: Escribir texto directamente
# ===========================================================================
with tab_direct:
    st.markdown("### ✏️ Ingresa el texto a sintetizar")
    st.caption(
        "Pega o escribe aquí el texto que deseas convertir a voz. "
        "Útil cuando no necesitas procesar un PDF completo."
    )

    # Panel de texto siempre visible (con key fija para preservar el contenido)
    direct_text = st.text_area(
        "Texto a sintetizar",
        key="direct_text_panel",
        height=220,
        help="El texto que escribas aquí se sintetizará directamente a voz.",
        label_visibility="collapsed",
    )

    # Contador
    char_count = len(direct_text)
    word_count = len(direct_text.split()) if direct_text.strip() else 0
    st.caption(f"📊 {char_count:,} caracteres · {word_count:,} palabras")

    # --- Botones de copiar/pegar/limpiar ---
    direct_text = render_text_actions(
        text_area_key="direct_text_panel",
        feedback_key="_direct_feedback",
        copy_button_key="btn_copy_direct",
        paste_button_key="btn_paste_direct",
        clear_button_key="btn_clear_direct",
    )

    # --- Generación de audio ---
    st.markdown("---")
    st.markdown("### 🔊 Generar audio")

    can_generate = bool(direct_text.strip()) and voice_is_ready(backend, voice)

    if not voice_is_ready(backend, voice):
        st.info("ℹ️ Descarga la voz Piper en la barra lateral primero.")

    if st.button(
        "🎙️ Generar audio",
        disabled=not can_generate,
        use_container_width=True,
        type="primary",
        key="btn_generate_direct",
    ):
        run_synthesis(
            text=direct_text,
            audio_key_prefix="direct",
            backend=backend,
            voice=voice,
            rate_percent=rate_percent,
            pitch_hz=pitch_hz,
            volume_percent=volume_percent,
            length_scale=length_scale,
            noise_scale=noise_scale,
            pitch_shift=pitch_shift,
            speed_pyttsx=speed_pyttsx,
        )

    # --- Reproductor ---
    render_player("direct", "texto_directo")
