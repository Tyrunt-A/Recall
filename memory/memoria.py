"""
Recall — Memory Manager
Dual-layer: short-term (in-memory historial) + long-term (JSON persistent).
"""

import json
import os
from datetime import datetime

from config import MEMORY_FILE, MAX_HISTORIAL, MAX_LONG_TERM

_historial = []  # Short-term: current session only

# ─── Resolve memory file path ───────────────────────────────────────────────────

def _ruta_memoria() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, MEMORY_FILE)


# ─── Long-term memory (JSON) ────────────────────────────────────────────────────

def _cargar_largo_plazo() -> list:
    ruta = _ruta_memoria()
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _guardar_largo_plazo(entradas: list):
    ruta = _ruta_memoria()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(entradas, f, ensure_ascii=False, indent=2)


def guardar_memoria(contenido: str, categoria: str = "general", etiquetas: list = None):
    """Persists a significant interaction to long-term memory."""
    entradas = _cargar_largo_plazo()

    entrada = {
        "id": len(entradas) + 1,
        "contenido": contenido,
        "categoria": categoria,
        "etiquetas": etiquetas or [],
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    entradas.append(entrada)

    if len(entradas) > MAX_LONG_TERM:
        entradas = entradas[-MAX_LONG_TERM:]

    _guardar_largo_plazo(entradas)


def buscar_memoria(query: str) -> list:
    """Simple keyword search over long-term memory."""
    entradas = _cargar_largo_plazo()
    if not query or not entradas:
        return []

    palabras = query.lower().split()
    resultados = []

    for e in entradas:
        texto = e.get("contenido", "").lower()
        if any(p in texto for p in palabras):
            resultados.append(e)

    return resultados[-10:]


def listar_memorias() -> list:
    return _cargar_largo_plazo()


def get_largo_plazo() -> list:
    return _cargar_largo_plazo()


# ─── Short-term memory (session historial) ──────────────────────────────────────

def get_historial() -> list:
    return list(_historial)


def agregar_turno(rol: str, contenido: str):
    """Adds a turn to the current session history."""
    _historial.append({"role": rol, "content": contenido})
    if len(_historial) > MAX_HISTORIAL * 2:
        del _historial[:-MAX_HISTORIAL * 2]


def limpiar_historial():
    _historial.clear()


# ─── Stats ───────────────────────────────────────────────────────────────────────

def stats() -> dict:
    largo = _cargar_largo_plazo()
    categorias = list(set(e.get("categoria", "") for e in largo))
    return {
        "turnos_historial": len(_historial),
        "entradas_largo_plazo": len(largo),
        "categorias": categorias
    }
