"""
Recall — File Reader Module
Handles reading of text files to inject as context.
"""

import os


SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".html"}
MAX_CHARS = 4000


def leer_archivo(ruta: str) -> str:
    """Reads a file and returns its content as a string (truncated if too long)."""
    if not os.path.exists(ruta):
        return f"[File not found: {ruta}]"

    ext = os.path.splitext(ruta)[-1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return f"[Unsupported file type: {ext}]"

    try:
        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()

        if len(contenido) > MAX_CHARS:
            contenido = contenido[:MAX_CHARS] + f"\n\n[Truncated — {len(contenido)} chars total]"

        return contenido

    except Exception as e:
        return f"[Error reading file: {str(e)}]"


def leer_directorio(ruta: str, extensiones: list = None) -> dict:
    """Reads all supported files in a directory. Returns {filename: content}."""
    if not os.path.isdir(ruta):
        return {}

    filtros = set(extensiones) if extensiones else SUPPORTED_EXTENSIONS
    resultado = {}

    for nombre in os.listdir(ruta):
        ext = os.path.splitext(nombre)[-1].lower()
        if ext in filtros:
            ruta_completa = os.path.join(ruta, nombre)
            resultado[nombre] = leer_archivo(ruta_completa)

    return resultado


def formatear_para_contexto(archivos: dict) -> str:
    """Formats a dict of {filename: content} into a readable context block."""
    if not archivos:
        return ""

    bloques = []
    for nombre, contenido in archivos.items():
        bloques.append(f"=== {nombre} ===\n{contenido}")

    return "\n\n".join(bloques)
