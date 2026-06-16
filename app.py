"""
Recall — Local Web Server
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

from core.agente import pensar, reflexionar, cerrar_sesion
from memory.memoria import (
    guardar_memoria, buscar_memoria,
    limpiar_historial, stats, listar_memorias
)
from config import TAGS

app = Flask(__name__, static_folder="web/static", template_folder="web")

_verbose = [False]
_sesion_iniciada = [False]


def _get_contexto_sesion() -> str:
    from datetime import datetime
    import json

    hoy = datetime.now()
    fecha_str = hoy.strftime("%A %d %B %Y")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    resumenes_path = os.path.join(base_dir, "memory", "resumenes.json")
    dias_str = "unknown"

    if os.path.exists(resumenes_path):
        try:
            with open(resumenes_path, "r", encoding="utf-8") as f:
                resumenes = json.load(f)
            if resumenes:
                ultima_fecha_str = resumenes[-1].get("fecha", "")
                if ultima_fecha_str:
                    ultima_fecha = datetime.strptime(ultima_fecha_str, "%Y-%m-%d")
                    dias = (hoy.date() - ultima_fecha.date()).days
                    if dias == 0:
                        dias_str = "today"
                    elif dias == 1:
                        dias_str = "1 day ago"
                    else:
                        dias_str = f"{dias} days ago"
        except Exception:
            pass

    return f"""[NEW SESSION]
Current date: {fecha_str}
Last session: {dias_str}
"""


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return jsonify({"error": "Empty message"}), 400

    if mensaje.startswith("/"):
        resultado = procesar_comando(mensaje)
        return jsonify({"tipo": "comando", "respuesta": resultado})

    try:
        ctx_sesion = ""
        if not _sesion_iniciada[0]:
            ctx_sesion = _get_contexto_sesion()
            _sesion_iniciada[0] = True

        respuesta = pensar(mensaje, verbose=_verbose[0], ctx_sesion=ctx_sesion)
        return jsonify({"tipo": "agente", "respuesta": respuesta})
    except Exception as e:
        return jsonify({"tipo": "error", "respuesta": str(e)}), 500


@app.route("/cerrar_sesion", methods=["POST"])
def endpoint_cerrar_sesion():
    data = request.get_json(silent=True) or {}
    persona = data.get("persona", "user")
    try:
        resultado = cerrar_sesion(persona=persona, verbose=_verbose[0])
        return jsonify({
            "status": "ok",
            "sesion_guardada": resultado["sesion_guardada"],
            "resumen": resultado["resumen"],
            "persona": resultado["persona"]
        })
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


@app.route("/memoria/stats", methods=["GET"])
def memoria_stats():
    return jsonify(stats())


@app.route("/memoria/buscar", methods=["POST"])
def memoria_buscar():
    data = request.get_json()
    query = data.get("query", "")
    return jsonify({"resultados": buscar_memoria(query)})


@app.route("/memoria/limpiar", methods=["POST"])
def memoria_limpiar():
    limpiar_historial()
    return jsonify({"ok": True})


@app.route("/verbose", methods=["POST"])
def toggle_verbose():
    _verbose[0] = not _verbose[0]
    return jsonify({"verbose": _verbose[0]})


def procesar_comando(cmd: str) -> str:
    partes = cmd.strip().split(" ", 2)
    comando = partes[0].lower()

    if comando == "/help":
        return "Commands: /memory save | search | list | stats | clear\n/verbose | /help"

    elif comando == "/verbose":
        _verbose[0] = not _verbose[0]
        return f"Verbose: {'ON' if _verbose[0] else 'OFF'}"

    elif comando == "/memory":
        subcomando = partes[1].lower() if len(partes) > 1 else ""

        if subcomando == "save":
            contenido = " ".join(partes[2:]) if len(partes) > 2 else ""
            if contenido:
                guardar_memoria(contenido, categoria="manual", etiquetas=["user"])
                return f"Saved: {contenido[:60]}"
            return "Usage: /memory save <text>"

        elif subcomando == "search":
            query = " ".join(partes[2:]) if len(partes) > 2 else ""
            if query:
                resultados = buscar_memoria(query)
                if resultados:
                    return "\n".join([f"[{r['id']}] {r['contenido'][:100]}" for r in resultados])
                return f"No results for '{query}'"
            return "Usage: /memory search <query>"

        elif subcomando == "list":
            memorias = listar_memorias()
            if memorias:
                return "\n".join([f"[{m['id']}] {m['contenido'][:80]}" for m in memorias[-20:]])
            return "No memories stored."

        elif subcomando == "stats":
            s = stats()
            return (
                f"History: {s['turnos_historial']} turns\n"
                f"Long-term: {s['entradas_largo_plazo']} entries\n"
                f"Categories: {', '.join(s['categorias']) or 'none'}"
            )

        elif subcomando == "clear":
            limpiar_historial()
            return "History cleared."

    return f"Unknown command: {comando}"


if __name__ == "__main__":
    print("\n  Recall — Web Interface")
    print("  Open your browser at: http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)