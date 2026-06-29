"""
tts_engine.py
=============
Motor de texto a voz para la aplicación de lectura de PDFs.

Diseño:
-------
Se exponen tres backends gratuitos, ordenados por calidad recomendada:

1. **Edge-TTS** (preferido)
   - Voces neuronales de Microsoft Edge Read Aloud vía API no oficial.
   - Calidad casi idéntica a Azure Cognitive Services.
   - 20+ voces en español (España + Latinoamérica).
   - Requiere conexión a internet (el texto se envía a servidores Microsoft).
   - Salida MP3 directamente reproducible por Streamlit.

2. **Piper TTS** (offline)
   - Voces neuronales en español de calidad media.
   - 100% offline una vez descargado el modelo de voz.
   - Requiere instalar el paquete `piper-tts` y descargar modelos .onnx.

3. **pyttsx3** (emergencia)
   - Usa las voces SAPI5 ya instaladas en Windows.
   - Cero descargas pero calidad robótica.
   - Solo como último recurso.

El motor detecta automáticamente cuál backend está disponible en el sistema
y permite cambiar entre ellos desde la interfaz.
"""

from __future__ import annotations

import asyncio
import io
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf


# ===========================================================================
# EDGE-TTS: voces neuronales Microsoft (calidad premium, requiere internet)
# ===========================================================================
# Voces neurales en español disponibles en Microsoft Edge Read Aloud.
# Fuente: https://learn.microsoft.com/azure/ai-services/speech-service/language-support
EDGE_VOICES: Dict[str, Dict[str, str]] = {
    # ---- España ----
    "🇪🇸 Elvira (España, femenina)": {
        "voice_id": "es-ES-ElviraNeural",
        "gender": "femenina",
        "country": "España",
    },
    "🇪🇸 Álvaro (España, masculino)": {
        "voice_id": "es-ES-AlvaroNeural",
        "gender": "masculino",
        "country": "España",
    },
    # ---- México ----
    "🇲🇽 Dalia (México, femenina)": {
        "voice_id": "es-MX-DaliaNeural",
        "gender": "femenina",
        "country": "México",
    },
    "🇲🇽 Jorge (México, masculino)": {
        "voice_id": "es-MX-JorgeNeural",
        "gender": "masculino",
        "country": "México",
    },
    # ---- Argentina ----
    "🇦🇷 Elena (Argentina, femenina)": {
        "voice_id": "es-AR-ElenaNeural",
        "gender": "femenina",
        "country": "Argentina",
    },
    "🇦🇷 Tomás (Argentina, masculino)": {
        "voice_id": "es-AR-TomasNeural",
        "gender": "masculino",
        "country": "Argentina",
    },
    # ---- Colombia ----
    "🇨🇴 Salomé (Colombia, femenina)": {
        "voice_id": "es-CO-SalomeNeural",
        "gender": "femenina",
        "country": "Colombia",
    },
    "🇨🇴 Gonzalo (Colombia, masculino)": {
        "voice_id": "es-CO-GonzaloNeural",
        "gender": "masculino",
        "country": "Colombia",
    },
    # ---- Chile ----
    "🇨🇱 Catalina (Chile, femenina)": {
        "voice_id": "es-CL-CatalinaNeural",
        "gender": "femenina",
        "country": "Chile",
    },
    "🇨🇱 Lorenzo (Chile, masculino)": {
        "voice_id": "es-CL-LorenzoNeural",
        "gender": "masculino",
        "country": "Chile",
    },
    # ---- Perú ----
    "🇵🇪 Camila (Perú, femenina)": {
        "voice_id": "es-PE-CamilaNeural",
        "gender": "femenina",
        "country": "Perú",
    },
    "🇵🇪 Miguel (Perú, masculino)": {
        "voice_id": "es-PE-MiguelNeural",
        "gender": "masculino",
        "country": "Perú",
    },
    # ---- Estados Unidos (español neutro) ----
    "🇺🇸 Paloma (EE.UU., femenina)": {
        "voice_id": "es-US-PalomaNeural",
        "gender": "femenina",
        "country": "EE.UU.",
    },
    "🇺🇸 Alonso (EE.UU., masculino)": {
        "voice_id": "es-US-AlonsoNeural",
        "gender": "masculino",
        "country": "EE.UU.",
    },
}


def is_edge_tts_available() -> bool:
    """Verifica si el paquete edge-tts está instalado."""
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


async def _edge_synthesize_async(
    text: str,
    voice_id: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> bytes:
    """
    Función asíncrona que sintetiza texto a MP3 con Edge-TTS.
    Devuelve los bytes MP3 completos.
    """
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_id,
        rate=rate,
        pitch=pitch,
        volume=volume,
    )

    audio_chunks: List[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    return b"".join(audio_chunks)


def synthesize_with_edge(
    text: str,
    voice_id: str,
    rate_percent: int = 0,
    pitch_hz: int = 0,
    volume_percent: int = 0,
) -> bytes:
    """
    Sintetiza texto a voz usando Edge-TTS.

    Parameters
    ----------
    text : str
        Texto a sintetizar.
    voice_id : str
        ID de la voz Edge (ej: "es-ES-ElviraNeural").
    rate_percent : int
        Ajuste de velocidad en porcentaje. -50 = más lento, +50 = más rápido.
    pitch_hz : int
        Ajuste de tono en Hz. -20 = más grave, +20 = más agudo.
    volume_percent : int
        Ajuste de volumen en porcentaje. -50 = más bajo, +50 = más alto.

    Returns
    -------
    bytes
        Audio en formato MP3.
    """
    rate = f"{'+' if rate_percent >= 0 else ''}{int(rate_percent)}%"
    pitch = f"{'+' if pitch_hz >= 0 else ''}{int(pitch_hz)}Hz"
    volume = f"{'+' if volume_percent >= 0 else ''}{int(volume_percent)}%"

    # Manejar el caso de estar dentro de un loop ya existente (Streamlit)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Streamlit no tiene un loop activo normalmente, pero por seguridad
            # creamos uno nuevo en un hilo separado.
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                audio_bytes = pool.submit(
                    asyncio.run,
                    _edge_synthesize_async(text, voice_id, rate, pitch, volume),
                ).result()
        else:
            audio_bytes = loop.run_until_complete(
                _edge_synthesize_async(text, voice_id, rate, pitch, volume)
            )
    except RuntimeError:
        # No hay event loop - crear uno nuevo
        audio_bytes = asyncio.run(
            _edge_synthesize_async(text, voice_id, rate, pitch, volume)
        )

    return audio_bytes


# ===========================================================================
# PIPER TTS: voces locales offline
# ===========================================================================
PIPER_VOICES: Dict[str, Dict[str, str]] = {
    "Femenina · sharvard (media)": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json",
        "model_file": "es_ES-sharvard-medium.onnx",
        "config_file": "es_ES-sharvard-medium.onnx.json",
        "gender": "femenina",
    },
    "Masculina · davefx (media)": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json",
        "model_file": "es_ES-davefx-medium.onnx",
        "config_file": "es_ES-davefx-medium.onnx.json",
        "gender": "masculina",
    },
    "Masculina · carlfm (baja)": {
        "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/x_low/es_ES-carlfm-x_low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/x_low/es_ES-carlfm-x_low.onnx.json",
        "model_file": "es_ES-carlfm-x_low.onnx",
        "config_file": "es_ES-carlfm-x_low.onnx.json",
        "gender": "masculina",
    },
}

VOICES_DIR = Path(__file__).parent / "voces"


def get_voices_dir() -> Path:
    """Devuelve (creando si hace falta) el directorio de voces Piper."""
    VOICES_DIR.mkdir(exist_ok=True)
    return VOICES_DIR


def is_piper_available() -> bool:
    """Verifica si el paquete piper-tts está instalado."""
    try:
        import piper  # noqa: F401
        return True
    except ImportError:
        return False


def is_pyttsx3_available() -> bool:
    """Verifica si pyttsx3 está disponible (siempre True en Windows)."""
    try:
        import pyttsx3  # noqa: F401
        return True
    except ImportError:
        return False


def list_available_backends() -> List[str]:
    """
    Devuelve la lista de backends TTS instalados en el sistema,
    ordenados por prioridad de calidad.
    """
    backends: List[str] = []
    if is_edge_tts_available():
        backends.append("Edge-TTS (online, alta calidad)")
    if is_piper_available():
        backends.append("Piper TTS (offline)")
    if is_pyttsx3_available():
        backends.append("pyttsx3 (Windows SAPI5, baja calidad)")
    return backends


# ---------------------------------------------------------------------------
# Gestión de descarga de voces Piper.
# ---------------------------------------------------------------------------
def is_voice_downloaded(voice_name: str) -> bool:
    """Indica si el modelo de voz Piper ya está descargado localmente."""
    if voice_name not in PIPER_VOICES:
        return False
    voice = PIPER_VOICES[voice_name]
    model_path = get_voices_dir() / voice["model_file"]
    config_path = get_voices_dir() / voice["config_file"]
    return model_path.exists() and config_path.exists()


def download_piper_voice(
    voice_name: str, progress_callback=None
) -> Tuple[bool, str]:
    """Descarga un modelo de voz Piper desde HuggingFace."""
    if voice_name not in PIPER_VOICES:
        return False, f"Voz desconocida: {voice_name}"

    voice = PIPER_VOICES[voice_name]
    voices_dir = get_voices_dir()
    model_path = voices_dir / voice["model_file"]
    config_path = voices_dir / voice["config_file"]

    def _report(block_num, block_size, total_size):
        if progress_callback and total_size > 0:
            percent = min(100, int(block_num * block_size * 100 / total_size))
            progress_callback(percent, f"Descargando {voice_name}...")

    try:
        if not model_path.exists():
            if progress_callback:
                progress_callback(0, f"Descargando modelo {voice_name}...")
            urllib.request.urlretrieve(voice["model_url"], model_path, _report)

        if not config_path.exists():
            urllib.request.urlretrieve(voice["config_url"], config_path)

        return True, f"Voz {voice_name} descargada correctamente."
    except Exception as exc:
        if model_path.exists():
            model_path.unlink()
        return False, f"Error al descargar la voz: {exc}"


# ===========================================================================
# Funciones de síntesis - Piper y pyttsx3
# ===========================================================================
def synthesize_with_piper(
    text: str,
    voice_name: str,
    length_scale: float = 1.0,
    noise_scale: float = 0.667,
    noise_w: float = 0.333,
    pitch_shift: float = 0.0,
) -> Tuple[int, np.ndarray]:
    """Sintetiza texto a voz usando Piper TTS. Devuelve (sample_rate, array)."""
    import wave

    from piper import PiperVoice

    voice_info = PIPER_VOICES[voice_name]
    model_path = get_voices_dir() / voice_info["model_file"]
    config_path = get_voices_dir() / voice_info["config_file"]

    voice = PiperVoice.load(str(model_path), config_path=str(config_path))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    buffer.seek(0)
    audio, sample_rate = sf.read(buffer, dtype="float32")

    if pitch_shift != 0.0 and len(audio) > 0:
        audio = _apply_pitch_shift(audio, sample_rate, pitch_shift)

    return sample_rate, audio


def synthesize_with_pyttsx3(
    text: str,
    voice_id: Optional[str] = None,
    rate: int = 0,
    volume: float = 1.0,
) -> Tuple[int, np.ndarray]:
    """Sintetiza texto a voz usando pyttsx3 (Windows SAPI5)."""
    import pyttsx3

    engine = pyttsx3.init()

    voices = engine.getProperty("voices")
    if voice_id:
        for v in voices:
            if voice_id in v.id or voice_id in v.name:
                engine.setProperty("voice", v.id)
                break
    else:
        for v in voices:
            if "spanish" in v.name.lower() or "español" in v.name.lower():
                engine.setProperty("voice", v.id)
                break

    engine.setProperty("rate", 200 + rate)
    engine.setProperty("volume", max(0.0, min(1.0, volume)))

    tmp_path = Path(tempfile.gettempdir()) / "pyttsx3_output.wav"
    engine.save_to_file(text, str(tmp_path))
    engine.runAndWait()
    engine.stop()

    if not tmp_path.exists():
        return 22050, np.zeros(0, dtype="float32")

    audio, sample_rate = sf.read(str(tmp_path), dtype="float32")
    tmp_path.unlink(missing_ok=True)

    return sample_rate, audio


def list_pyttsx3_voices() -> List[Dict[str, str]]:
    """Lista las voces Windows SAPI5 disponibles (filtradas por español)."""
    try:
        import pyttsx3

        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.stop()

        result = []
        for v in voices:
            name = v.name
            if any(keyword in name.lower() for keyword in
                   ["spanish", "español", "es-", "es_", "helena", "sabina",
                    "pablo", "helmut"]):
                result.append({"id": v.id, "name": name})
        return result
    except Exception:
        return []


# ===========================================================================
# Utilidades de procesamiento de audio.
# ===========================================================================
def _apply_pitch_shift(
    audio: np.ndarray, sample_rate: int, semitones: float
) -> np.ndarray:
    """Cambio de tono simple basado en resampling (sin dependencias externas)."""
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    factor = 2.0 ** (semitones / 12.0)
    new_length = int(len(audio) / factor)

    if new_length < 2:
        return audio

    indices = np.linspace(0, len(audio) - 1, new_length)
    shifted = np.interp(indices, np.arange(len(audio)), audio)

    return shifted.astype("float32")


def concatenate_audio(segments: List[Tuple[int, np.ndarray]]) -> Tuple[int, np.ndarray]:
    """Concatena múltiples segmentos de audio WAV en uno solo."""
    if not segments:
        return 22050, np.zeros(0, dtype="float32")

    sample_rate = segments[0][0]
    arrays = [seg[1] for seg in segments]

    normalized = []
    for arr in arrays:
        if arr.ndim > 1:
            arr = arr.mean(axis=1)
        normalized.append(arr)

    return sample_rate, np.concatenate(normalized) if normalized else np.zeros(0)


def audio_to_wav_bytes(sample_rate: int, audio: np.ndarray) -> bytes:
    """Convierte un array de audio a bytes WAV en memoria."""
    buffer = io.BytesIO()
    if audio.dtype != "float32":
        audio = audio.astype("float32")
    sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def concatenate_mp3_chunks(mp3_chunks: List[bytes]) -> bytes:
    """
    Concatena múltiples fragmentos MP3 en un solo stream MP3.
    Los headers MP3 permiten la concatenación binaria directa para reproducción.
    """
    return b"".join(mp3_chunks)
