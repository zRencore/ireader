"""
pdf_processor.py
================
Módulo para extracción de texto nativo de archivos PDF.

Utiliza pypdf (librería gratuita y de código abierto) para leer PDFs
digitales (aquellos donde el texto es seleccionable). No incluye soporte
para PDFs escaneados que requieran OCR, ya que el alcance del proyecto
se limita a PDFs con texto nativo.
"""

from __future__ import annotations

import io
from typing import List, Dict

from pypdf import PdfReader


def extract_pages_from_pdf(pdf_file_bytes: bytes) -> List[Dict[str, object]]:
    """
    Extrae el texto de cada página de un PDF digital.

    Parameters
    ----------
    pdf_file_bytes : bytes
        Contenido binario del PDF cargado en memoria.

    Returns
    -------
    list[dict]
        Lista de diccionarios con la forma:
        [{"page_number": 1, "text": "...", "char_count": 123}, ...]
        Las páginas sin texto extraíble devuelven text="".
    """
    reader = PdfReader(io.BytesIO(pdf_file_bytes))
    pages: List[Dict[str, object]] = []

    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            # Algunas páginas pueden fallar por codificación o fuentes embebidas
            # incompletas. En lugar de romper el flujo, devolvemos cadena vacía.
            text = ""

        pages.append(
            {
                "page_number": index,
                "text": text.strip(),
                "char_count": len(text.strip()),
            }
        )

    return pages


def extract_full_text(pages: List[Dict[str, object]]) -> str:
    """
    Concatena el texto de todas las páginas en un solo string,
    separando cada página con un doble salto de línea.
    """
    return "\n\n".join(page["text"] for page in pages if page["text"])


def get_document_stats(pages: List[Dict[str, object]]) -> Dict[str, int]:
    """
    Calcula estadísticas básicas del documento extraído.
    Útil para mostrar al usuario antes de iniciar la lectura.
    """
    total_chars = sum(int(page["char_count"]) for page in pages)
    total_words = sum(len(str(page["text"]).split()) for page in pages)
    non_empty_pages = sum(1 for page in pages if page["text"])

    return {
        "total_pages": len(pages),
        "pages_with_text": non_empty_pages,
        "total_chars": total_chars,
        "total_words": total_words,
        "estimated_minutes": max(1, total_words // 150),  # ~150 ppm en español
    }


def split_text_into_chunks(text: str, max_chars: int = 500) -> List[str]:
    """
    Divide un texto largo en fragmentos más pequeños respetando los límites
    de oración. Piper TTS tiene un límite práctico de longitud por síntesis,
    por lo que conviene procesar en fragmentos de ~500 caracteres.

    Parameters
    ----------
    text : str
        Texto a dividir.
    max_chars : int
        Tamaño máximo aproximado de cada fragmento.
    """
    if not text.strip():
        return []

    # Dividir primero por puntos, signos de exclamación y de interrogación.
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Si una sola oración excede el límite, la cortamos por comas.
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            sub_parts = sentence.split(",")
            sub_chunk = ""
            for part in sub_parts:
                if len(sub_chunk) + len(part) + 1 > max_chars:
                    if sub_chunk:
                        chunks.append(sub_chunk.strip())
                    sub_chunk = part
                else:
                    sub_chunk = f"{sub_chunk}, {part}".strip(", ")
            if sub_chunk:
                chunks.append(sub_chunk.strip())
            continue

        if len(current_chunk) + len(sentence) + 1 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = f"{current_chunk} {sentence}".strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
