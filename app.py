"""
app.py
======
Aplicación Streamlit para la lectura de PDFs con voz.

Estilo visual: minimalista moderno, blanco/azul, inspirado en Notion.
Soporta tres backends de TTS:
  - Edge-TTS (online, máxima calidad, recomendado)
  - Piper TTS (offline, calidad media)
  - pyttsx3 (offline, calidad baja, solo emergencia)

Uso:
    streamlit run app.py
"""

from __future__ import annotations

import time
from typing import Dict, List

import streamlit as st

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
# Estilos CSS para una apariencia minimalista estilo Notion.
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter",
                     "Helvetica Neue", Arial, sans-serif;
        background-color: #FFFFFF;
        color: #1F2937;
    }
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        color: #111827 !important;
    }
    h2, h3 {
        color: #1F2937 !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }
    .stButton > button {
        background-color: #2563EB;
        color: white;
        border: none;
        padding: 0.55rem 1.1rem;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.92rem;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        background-color: #1D4ED8;
        transform: translateY(-1px);
    }
    .stButton > button:disabled {
        background-color: #D1D5DB;
        color: #6B7280;
        cursor: not-allowed;
        transform: none;
    }
    .stButton > button[kind="secondary"] {
        background-color: #F3F4F6;
        color: #374151;
        border: 1px solid #E5E7EB;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #E5E7EB;
    }
    section[data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid #E5E7EB;
    }
    [data-testid="stMetric"] {
        background-color: #F9FAFB;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #F3F4F6;
    }
    [data-testid="stMetricValue"] {
        color: #2563EB !important;
        font-weight: 700 !important;
    }
    .stSlider > div > div > div > div {
        background-color: #2563EB !important;
    }
    .stSelectbox > div > div {
        border-radius: 6px !important;
        border-color: #E5E7EB !important;
    }
    [data-testid="stFileUploader"] {
        border: 2px dashed #E5E7EB !important;
        border-radius: 8px !important;
        background-color: #FAFAFA !important;
        padding: 1.5rem !important;
    }
    .stAlert > div {
        border-radius: 6px !important;
    }
    audio {
        width: 100% !important;
    }
    .block-container {
        padding-top: 2.5rem !important;
        max-width: 1100px;
    }
    hr {
        border-color: #F3F4F6 !important;
        margin: 1.5rem 0 !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6B7280 !important;
        font-size: 0.85rem !important;
    }
    .backend-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 6px;
    }
    .badge-online {
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    .badge-offline {
        background-color: #DCFCE7;
        color: #166534;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Estado de la sesión (memoria temporal, no persistente)
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    defaults = {
        "pdf_pages": [],
        "pdf_filename": None,
        "selected_voice": None,
        "selected_backend": None,
        "audio_bytes": None,
        "audio_format": "audio/wav",
        "current_chunk_index": 0,
        "chunks": [],
        "processing": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ---------------------------------------------------------------------------
# Barra lateral: configuración de voz y motor TTS
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Configuración")

    backends = tts_engine.list_available_backends()
    if not backends:
        st.error(
            "No se detectó ningún motor TTS instalado. "
            "Instala las dependencias con `pip install -r requirements.txt`."
        )
        st.stop()
    elif not tts_engine.is_edge_tts_available():
        st.warning(
            "Edge-TTS no está instalado en este entorno, por eso no aparece en la lista. "
            "Instala las dependencias con `pip install -r requirements.txt`."
        )

    # Marcar Edge-TTS como recomendado si está disponible
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

    # Badge online/offline
    if "Edge-TTS" in selected_backend:
        st.caption("🌐 <span class='backend-badge badge-online'>Online</span>",
                   unsafe_allow_html=True)
        st.caption("Calidad alta · Requiere conexión a internet")
    elif "Piper" in selected_backend:
        st.caption("🔒 <span class='backend-badge badge-offline'>Offline</span>",
                   unsafe_allow_html=True)
        st.caption("Calidad media · Funciona sin internet")
    else:
        st.caption("🔒 <span class='backend-badge badge-offline'>Offline</span>",
                   unsafe_allow_html=True)
        st.caption("Calidad baja · Solo emergencia")

    st.markdown("---")

    # =====================================================================
    # CONFIGURACIÓN EDGE-TTS
    # =====================================================================
    if "Edge-TTS" in selected_backend:
        st.markdown("### 🎙️ Voz Edge-TTS")

        voice_options = list(tts_engine.EDGE_VOICES.keys())
        selected_voice = st.selectbox(
            "Selecciona una voz",
            options=voice_options,
            index=0,
            help="14 voces neurales en español de diferentes países.",
        )
        st.session_state["selected_voice"] = selected_voice

        voice_info = tts_engine.EDGE_VOICES[selected_voice]
        st.caption(
            f"**{voice_info['gender'].capitalize()}** · "
            f"País: **{voice_info['country']}** · "
            f"ID: `{voice_info['voice_id']}`"
        )

        # Filtro rápido por país
        countries = sorted(set(v["country"] for v in tts_engine.EDGE_VOICES.values()))
        selected_country = st.selectbox(
            "Filtrar por país",
            options=["Todos"] + countries,
            help="Filtra el selector de arriba (no recarga la página)."
        )

        # Si se selecciona un país, ajustar las opciones visibles
        if selected_country != "Todos":
            filtered_voices = [
                name for name, info in tts_engine.EDGE_VOICES.items()
                if info["country"] == selected_country
            ]
            if filtered_voices:
                selected_voice = st.selectbox(
                    "Voz filtrada",
                    options=filtered_voices,
                    key="voice_filtered",
                )
                st.session_state["selected_voice"] = selected_voice
                voice_info = tts_engine.EDGE_VOICES[selected_voice]
                st.caption(
                    f"**{voice_info['gender'].capitalize()}** · "
                    f"País: **{voice_info['country']}**"
                )

        st.markdown("---")
        st.markdown("### 🎛️ Ajustes de voz")

        # Velocidad
        rate_percent = st.slider(
            "Velocidad de lectura (%)",
            min_value=-50,
            max_value=100,
            value=0,
            step=5,
            help="0 = velocidad normal. +50 = 50% más rápido. -50 = 50% más lento.",
        )

        # Tono
        pitch_hz = st.slider(
            "Tono (Hz)",
            min_value=-20,
            max_value=20,
            value=0,
            step=1,
            help="0 = tono original. Positivo = más agudo. Negativo = más grave.",
        )

        # Volumen
        volume_percent = st.slider(
            "Volumen (%)",
            min_value=-50,
            max_value=50,
            value=0,
            step=5,
            help="0 = volumen normal. Positivo = más alto.",
        )

        # Variables que se usarán en la generación
        length_scale = 1.0
        noise_scale = 0.0
        speed_pyttsx = 0

    # =====================================================================
    # CONFIGURACIÓN PIPER
    # =====================================================================
    elif "Piper" in selected_backend:
        st.markdown("### 🎙️ Voces Piper (español)")

        voice_options = list(tts_engine.PIPER_VOICES.keys())
        selected_voice = st.selectbox(
            "Selecciona una voz",
            options=voice_options,
            help="Voces neuronales gratuitas en español (offline).",
        )
        st.session_state["selected_voice"] = selected_voice

        voice_info = tts_engine.PIPER_VOICES[selected_voice]
        st.caption(
            f"Género: **{voice_info['gender']}**"
        )

        if not tts_engine.is_voice_downloaded(selected_voice):
            st.warning("Esta voz no está descargada todavía.")
            if st.button("⬇️ Descargar voz (~60 MB)", use_container_width=True):
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

        speed = st.slider(
            "Velocidad de lectura",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.05,
            help="1.0 = velocidad normal.",
        )
        length_scale = 1.0 / speed

        pitch_shift = st.slider(
            "Tono (semitonos)",
            min_value=-6.0,
            max_value=6.0,
            value=0.0,
            step=0.5,
        )

        noise_scale = st.slider(
            "Expresividad",
            min_value=0.0,
            max_value=1.0,
            value=0.667,
            step=0.05,
        )

        rate_percent = 0
        pitch_hz = 0
        volume_percent = 0
        speed_pyttsx = 0

    # =====================================================================
    # CONFIGURACIÓN PYTTSX3
    # =====================================================================
    else:
        st.markdown("### 🎙️ Voces Windows (SAPI5)")

        sapi_voices = tts_engine.list_pyttsx3_voices()
        if sapi_voices:
            voice_names = [v["name"] for v in sapi_voices]
            selected_idx = st.selectbox(
                "Selecciona una voz",
                options=range(len(voice_names)),
                format_func=lambda i: voice_names[i],
            )
            st.session_state["selected_voice"] = sapi_voices[selected_idx]["id"]
            st.caption(f"Voz: {voice_names[selected_idx]}")
        else:
            st.info(
                "No se detectaron voces en español instaladas en Windows. "
                "Se usará la voz por defecto del sistema."
            )
            st.session_state["selected_voice"] = None

        st.markdown("---")
        st.markdown("### 🎛️ Ajustes de voz")

        speed_pyttsx = st.slider(
            "Velocidad (palabras por minuto adicional)",
            min_value=-50,
            max_value=100,
            value=0,
            step=10,
        )
        rate_percent = 0
        pitch_hz = 0
        volume_percent = 0
        length_scale = 1.0
        noise_scale = 0.0
        pitch_shift = 0.0

    st.markdown("---")
    st.markdown("### ℹ️ Acerca de")
    st.caption(
        "Aplicación local para lectura de PDFs con voz. "
        "Edge-TTS requiere internet; Piper y pyttsx3 funcionan offline."
    )


# ---------------------------------------------------------------------------
# Contenido principal
# ---------------------------------------------------------------------------
st.title("📚 Lector de PDF con Voz")
st.caption(
    "Sube un PDF digital en español y escúchalo con voces sintéticas locales."
)

uploaded_file = st.file_uploader(
    "Arrastra tu PDF aquí o haz clic para seleccionar",
    type=["pdf"],
    help="Solo se admiten PDFs digitales (con texto seleccionable).",
)

if uploaded_file is not None:
    if st.session_state["pdf_filename"] != uploaded_file.name:
        with st.spinner("Extrayendo texto del PDF..."):
            pdf_bytes = uploaded_file.getvalue()
            try:
                pages = extract_pages_from_pdf(pdf_bytes)
                st.session_state["pdf_pages"] = pages
                st.session_state["pdf_filename"] = uploaded_file.name
                st.session_state["audio_bytes"] = None
                st.session_state["current_chunk_index"] = 0
                st.session_state["chunks"] = []
            except Exception as exc:
                st.error(f"No se pudo procesar el PDF: {exc}")
                st.stop()

    pages = st.session_state["pdf_pages"]
    stats = get_document_stats(pages)

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
            min_value=start_page,
            max_value=stats["total_pages"],
            value=stats["total_pages"],
            step=1,
        )

    selected_pages = pages[start_page - 1 : end_page]
    full_text = extract_full_text(selected_pages)

    with st.expander("Ver texto extraído", expanded=False):
        if full_text.strip():
            st.text_area(
                "Texto a leer",
                value=full_text,
                height=250,
                label_visibility="collapsed",
            )
        else:
            st.warning(
                "No se pudo extraer texto de las páginas seleccionadas. "
                "Es posible que el PDF sea escaneado (imagen) y requiera OCR, "
                "lo cual está fuera del alcance de esta versión."
            )

    st.markdown("---")

    # =====================================================================
    # GENERACIÓN DE AUDIO
    # =====================================================================
    st.markdown("### 🔊 Generar audio")

    # Verificar disponibilidad de voz según backend
    can_generate = bool(full_text.strip())
    backend = st.session_state["selected_backend"]
    voice = st.session_state["selected_voice"]

    if "Edge-TTS" in backend:
        # Edge-TTS siempre disponible (no requiere descarga)
        pass
    elif "Piper" in backend:
        if not voice or not tts_engine.is_voice_downloaded(voice):
            can_generate = False
    # pyttsx3: can_generate ya es True si hay texto

    if not can_generate:
        st.info(
            "Configura una voz disponible en la barra lateral antes de generar audio."
        )

    if st.button(
        "🎙️ Generar audio",
        disabled=not can_generate,
        use_container_width=True,
        type="primary",
    ):
        chunks = split_text_into_chunks(full_text, max_chars=500)
        st.session_state["chunks"] = chunks

        if not chunks:
            st.warning("No hay texto para sintetizar.")
        else:
            progress = st.progress(0, "Preparando síntesis...")

            # Caso Edge-TTS: produce MP3
            if "Edge-TTS" in backend:
                mp3_chunks: List[bytes] = []
                voice_id = tts_engine.EDGE_VOICES[voice]["voice_id"]

                for i, chunk in enumerate(chunks):
                    progress.progress(
                        int((i / len(chunks)) * 100),
                        f"Sintetizando fragmento {i + 1} de {len(chunks)} con Edge-TTS...",
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
                    except Exception as exc:
                        st.warning(f"Error en fragmento {i + 1}: {exc}")

                if mp3_chunks:
                    progress.progress(95, "Concatenando audio MP3...")
                    final_mp3 = tts_engine.concatenate_mp3_chunks(mp3_chunks)
                    st.session_state["audio_bytes"] = final_mp3
                    st.session_state["audio_format"] = "audio/mp3"
                    progress.progress(100, "✅ Audio listo")
                    time.sleep(0.5)
                    progress.empty()
                    st.success("Audio generado correctamente con Edge-TTS.")
                else:
                    progress.empty()
                    st.error("No se pudo generar audio. Verifica tu conexión a internet.")

            # Caso Piper: produce WAV
            elif "Piper" in backend:
                audio_segments: List = []
                for i, chunk in enumerate(chunks):
                    progress.progress(
                        int((i / len(chunks)) * 100),
                        f"Sintetizando fragmento {i + 1} de {len(chunks)} con Piper...",
                    )
                    try:
                        sr, audio = tts_engine.synthesize_with_piper(
                            text=chunk,
                            voice_name=voice,
                            length_scale=length_scale,
                            noise_scale=noise_scale,
                            pitch_shift=pitch_shift if 'pitch_shift' in dir() else 0.0,
                        )
                        if len(audio) > 0:
                            audio_segments.append((sr, audio))
                    except Exception as exc:
                        st.warning(f"Error en fragmento {i + 1}: {exc}")

                if audio_segments:
                    progress.progress(95, "Concatenando audio WAV...")
                    final_sr, final_audio = tts_engine.concatenate_audio(audio_segments)
                    wav_bytes = tts_engine.audio_to_wav_bytes(final_sr, final_audio)
                    st.session_state["audio_bytes"] = wav_bytes
                    st.session_state["audio_format"] = "audio/wav"
                    progress.progress(100, "✅ Audio listo")
                    time.sleep(0.5)
                    progress.empty()
                    st.success("Audio generado correctamente con Piper.")
                else:
                    progress.empty()
                    st.error("No se pudo generar audio.")

            # Caso pyttsx3
            else:
                audio_segments: List = []
                for i, chunk in enumerate(chunks):
                    progress.progress(
                        int((i / len(chunks)) * 100),
                        f"Sintetizando fragmento {i + 1} de {len(chunks)} con pyttsx3...",
                    )
                    try:
                        sr, audio = tts_engine.synthesize_with_pyttsx3(
                            text=chunk,
                            voice_id=voice,
                            rate=speed_pyttsx,
                        )
                        if len(audio) > 0:
                            audio_segments.append((sr, audio))
                    except Exception as exc:
                        st.warning(f"Error en fragmento {i + 1}: {exc}")

                if audio_segments:
                    progress.progress(95, "Concatenando audio WAV...")
                    final_sr, final_audio = tts_engine.concatenate_audio(audio_segments)
                    wav_bytes = tts_engine.audio_to_wav_bytes(final_sr, final_audio)
                    st.session_state["audio_bytes"] = wav_bytes
                    st.session_state["audio_format"] = "audio/wav"
                    progress.progress(100, "✅ Audio listo")
                    time.sleep(0.5)
                    progress.empty()
                    st.success("Audio generado correctamente.")
                else:
                    progress.empty()
                    st.error("No se pudo generar audio.")

    # =====================================================================
    # REPRODUCTOR
    # =====================================================================
    if st.session_state.get("audio_bytes"):
        st.markdown("---")
        st.markdown("### ▶️ Reproductor")

        audio_fmt = st.session_state.get("audio_format", "audio/wav")
        file_ext = "mp3" if "mp3" in audio_fmt else "wav"
        st.audio(st.session_state["audio_bytes"], format=audio_fmt)

        st.download_button(
            label=f"💾 Descargar audio (.{file_ext.upper()})",
            data=st.session_state["audio_bytes"],
            file_name=f"{st.session_state['pdf_filename'] or 'audio'}.{file_ext}",
            mime=audio_fmt,
            use_container_width=True,
        )

else:
    st.markdown("---")
    st.markdown("### 🚀 Cómo usar esta aplicación")
    st.markdown(
        """
1. **Sube un PDF digital** (con texto seleccionable) en el área superior.
2. **Configura la voz** en la barra lateral:
   - **Edge-TTS** (recomendado): 14 voces en español, calidad alta, requiere internet.
   - **Piper TTS**: voces locales, calidad media, sin internet.
   - **pyttsx3**: emergencia, calidad baja.
3. **Selecciona el rango de páginas** que deseas escuchar.
4. Haz clic en **Generar audio** y reproduce o descarga el resultado.

> 🔒 **Privacidad**: Edge-TTS envía el texto a servidores Microsoft.
>    Piper y pyttsx3 funcionan 100% offline.
        """
    )
