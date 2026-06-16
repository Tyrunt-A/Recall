"""
Recall — Memory Manager
Handles conversation history (short-term) and episodic memory (long-term).
"""

import json
import os
from datetime import datetime
from typing import Optional
from config import MEMORY_FILE, MAX_HISTORIAL, MAX_LONG_TERM


def _get_memory_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, MEMORY_FILE)


def _load_raw() -> dict:
    path = _get_memory_path()
    if not os.path.exists(path):
        return {"historial": [], "largo_plazo": [], "metadata": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_raw(data: dict) -> None:
    path = _get_memory_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_historial() -> list[dict]:
    data = _load_raw()
    return data["historial"][-MAX_HISTORIAL:]


def agregar_turno(rol: str, contenido: str, nombre: Optional[str] = None) -> None:
    data = _load_raw()
    entrada = {
        "role": rol,
        "content": contenido,
        "timestamp": datetime.now().isoformat()
    }
    if nombre:
        entrada["name"] = nombre
    data["historial"].append(entrada)
    if len(data["historial"]) > MAX_HISTORIAL * 2:
        data["historial"] = data["historial"][-MAX_HISTORIAL:]
    _save_raw(data)


def get_historial_para_api() -> list[dict]:
    historial = get_historial()
    mensajes = []
    for entry in historial:
        mensajes.append({"role": entry["role"], "content": entry["content"]})
    return mensajes


def guardar_memoria(contenido: str, categoria: str = "general", etiquetas: list[str] = None) -> None:
    data = _load_raw()
    entrada = {
        "id": len(data["largo_plazo"]) + 1,
        "contenido": contenido,
        "categoria": categoria,
        "etiquetas": etiquetas or [],
        "timestamp": datetime.now().isoformat()
    }
    data["largo_plazo"].append(entrada)
    if len(data["largo_plazo"]) > MAX_LONG_TERM:
        data["largo_plazo"] = data["largo_plazo"][-MAX_LONG_TERM:]
    _save_raw(data)


def buscar_memoria(query: str, limite: int = 5) -> list[dict]:
    data = _load_raw()
    query_lower = query.lower()
    resultados = [
        e for e in data["largo_plazo"]
        if query_lower in e["contenido"].lower()
        or any(query_lower in tag.lower() for tag in e.get("etiquetas", []))
    ]
    return resultados[-limite:]


def listar_memorias(categoria: Optional[str] = None) -> list[dict]:
    data = _load_raw()
    memorias = data["largo_plazo"]
    if categoria:
        memorias = [m for m in memorias if m.get("categoria") == categoria]
    return memorias


def limpiar_historial() -> None:
    data = _load_raw()
    data["historial"] = []
    _save_raw(data)


def stats() -> dict:
    data = _load_raw()
    return {
        "turnos_historial": len(data["historial"]),
        "entradas_largo_plazo": len(data["largo_plazo"]),
        "categorias": list({m.get("categoria", "?") for m in data["largo_plazo"]})
    }