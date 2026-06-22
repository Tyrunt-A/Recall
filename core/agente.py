"""
Recall — Main Cognitive Loop
"""

import threading
import anthropic
import os

from config import MODEL, MODEL_HAIKU, MAX_TOKENS, TEMPERATURE, TAGS
from core.prompt import SYSTEM_PROMPT
from memory.memoria import (
    get_historial, agregar_turno,
    buscar_memoria, guardar_memoria,
    get_largo_plazo, limpiar_historial
)

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


# ─── Context loader ────────────────────────────────────────────────────────────

def _cargar_contexto(mensaje: str) -> str:
    """Pulls relevant long-term memory entries for the current message."""
    resultados = buscar_memoria(mensaje)
    if not resultados:
        return ""
    lineas = [f"- {r['contenido']}" for r in resultados[:5]]
    return "[Relevant memory]\n" + "\n".join(lineas)


# ─── Bias detector ─────────────────────────────────────────────────────────────

def _detectar_patrones() -> str:
    """Identifies active behavioral patterns from recent history."""
    historial = get_historial()
    if len(historial) < 2:
        return ""

    reciente = " ".join([t.get("content", "") for t in historial[-4:]])
    etiquetas_activas = []

    keywords = {
        "analytical":  ["why", "how", "because", "reason", "pattern", "analyze"],
        "explorer":    ["try", "what if", "curious", "test", "idea", "maybe"],
        "cautious":    ["not sure", "worried", "feel", "afraid", "but", "however"],
        "focused":     ["finish", "deadline", "goal", "need to", "must", "project"],
        "undecided":   ["don't know", "either", "or maybe", "confused", "unsure"],
        "calculated":  ["risk", "worth", "trade-off", "cost", "benefit", "decide"],
    }

    for tag, words in keywords.items():
        if any(w in reciente.lower() for w in words):
            etiquetas_activas.append(f"{tag}: {TAGS[tag]}")

    if not etiquetas_activas:
        return ""

    return "[Active patterns]\n" + "\n".join(f"- {e}" for e in etiquetas_activas)


# ─── Background classifier (Haiku) ─────────────────────────────────────────────

def _clasificar_async(mensaje: str, respuesta: str):
    """Runs Haiku silently in background to decide if interaction is worth storing."""
    def _run():
        try:
            client = _get_client()
            prompt = (
                f"User said: {mensaje}\n"
                f"Agent replied: {respuesta}\n\n"
                "Evaluate this exchange. Reply with JSON only, no explanation:\n"
                '{"worth_storing": true/false, "summary": "one sentence max", '
                '"tags": ["tag1", "tag2"]}'
            )
            result = client.messages.create(
                model=MODEL_HAIKU,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            import json
            text = result.content[0].text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            if data.get("worth_storing"):
                guardar_memoria(
                    data.get("summary", mensaje[:100]),
                    categoria="auto",
                    etiquetas=data.get("tags", [])
                )
        except Exception:
            pass  # Silent — never blocks the main thread

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# ─── Main think function ────────────────────────────────────────────────────────

def pensar(mensaje: str, verbose: bool = False, ctx_sesion: str = "") -> str:
    """Main entry point. Loads context, detects patterns, calls Sonnet, triggers classifier."""
    client = _get_client()

    contexto_memoria = _cargar_contexto(mensaje)
    patrones = _detectar_patrones()

    system = SYSTEM_PROMPT
    if ctx_sesion:
        system = ctx_sesion + "\n\n" + system
    if contexto_memoria:
        system += "\n\n" + contexto_memoria
    if patrones:
        system += "\n\n" + patrones

    agregar_turno("user", mensaje)
    historial = get_historial()

    if verbose:
        print(f"\n[CONTEXT]\n{contexto_memoria or '(none)'}")
        print(f"[PATTERNS]\n{patrones or '(none)'}")

    result = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system,
        messages=historial
    )

    respuesta = result.content[0].text
    agregar_turno("assistant", respuesta)

    _clasificar_async(mensaje, respuesta)

    return respuesta


# ─── Session close ──────────────────────────────────────────────────────────────

def cerrar_sesion(persona: str = "user", verbose: bool = False) -> dict:
    """Summarizes and archives the current session."""
    historial = get_historial()
    if not historial:
        return {"sesion_guardada": False, "resumen": "", "persona": persona}

    try:
        client = _get_client()
        contenido = "\n".join([
            f"{t['role'].upper()}: {t['content']}" for t in historial
        ])
        result = client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    f"Summarize this conversation in 2-3 sentences. "
                    f"Focus on what was discussed and any decisions made.\n\n{contenido}"
                )
            }]
        )
        resumen = result.content[0].text.strip()
    except Exception as e:
        resumen = f"Session ended. ({str(e)})"

    import json
    from datetime import datetime
    import os

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resumenes_path = os.path.join(base_dir, "memory", "resumenes.json")

    resumenes = []
    if os.path.exists(resumenes_path):
        try:
            with open(resumenes_path, "r", encoding="utf-8") as f:
                resumenes = json.load(f)
        except Exception:
            pass

    resumenes.append({
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M"),
        "persona": persona,
        "resumen": resumen,
        "turnos": len(historial)
    })

    with open(resumenes_path, "w", encoding="utf-8") as f:
        json.dump(resumenes, f, ensure_ascii=False, indent=2)

    limpiar_historial()

    if verbose:
        print(f"\n[SESSION CLOSED] {resumen}")

    return {"sesion_guardada": True, "resumen": resumen, "persona": persona}


# ─── Reflect (unused by default, available for future use) ─────────────────────

def reflexionar(tema: str = "") -> str:
    """Optional: asks the agent to reflect on accumulated memory."""
    largo_plazo = get_largo_plazo()
    if not largo_plazo:
        return "No memory to reflect on yet."

    client = _get_client()
    muestra = largo_plazo[-20:]
    contenido = "\n".join([f"- {m['contenido']}" for m in muestra])

    prompt = f"Based on these memory entries, identify 2-3 behavioral patterns:\n\n{contenido}"
    if tema:
        prompt += f"\n\nFocus on: {tema}"

    result = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return result.content[0].text
