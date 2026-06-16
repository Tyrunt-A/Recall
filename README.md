# Recall
### *A conversational agent that recalls, learns and echoes back*

Recall is a persistent-memory conversational agent built on top of Claude's API. It maintains context across sessions, identifies behavioral patterns over time, and adapts its responses based on accumulated knowledge of the user.

---

## What it does

Most AI assistants forget everything the moment you close the tab. Recall doesn't.

- **Persistent memory** — stores conversation history across sessions in structured long-term and short-term layers
- **Pattern recognition** — a silent background classifier (Claude Haiku) analyzes each interaction and tags behavioral signals without adding latency
- **Contextual adaptation** — the main model (Claude Sonnet) receives enriched context on every turn, making responses progressively more accurate
- **Session management** — every session is summarized and archived automatically on close
- **Vision support** — optional facial recognition layer to identify who is speaking

---

## Stack

| Layer | Technology |
|---|---|
| Main model | Claude Sonnet (Anthropic API) |
| Background classifier | Claude Haiku (async, zero latency) |
| Memory | JSON-based dual-layer (short-term + long-term) |
| Backend | Python + Flask |
| Vision | DeepFace + Facenet |
| Frontend | Vanilla HTML/CSS/JS |

---

## Architecture

```
USER INPUT
    ↓
CONTEXT LOADER       ← pulls relevant long-term memory
    ↓
BIAS DETECTOR        ← identifies active behavioral patterns
    ↓
SONNET (main)        ← generates response with enriched context
    ↓
RESPONSE
    ↓
HAIKU (background)   ← classifies interaction silently, no latency added
    ↓
MEMORY WRITER        ← persists if interaction is significant
```

---

## Setup

### Requirements

```bash
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### Run

```bash
python app.py
```

Open your browser at `http://localhost:5000`

---

## Project structure

```
recall/
├── app.py                  # Flask server + session management
├── config.py               # Model config and global parameters
├── requirements.txt
├── core/
│   ├── agente.py           # Main cognitive loop
│   ├── prompt.py           # System prompt (configurable)
│   └── lector.py           # File reader module
├── memory/
│   └── memoria.py          # Short and long-term memory manager
├── vision/
│   └── reconocimiento.py   # Optional facial recognition
└── web/
    └── index.html          # Web interface
```

---

## Key design decisions

**Dual-model architecture** — Sonnet handles conversation quality, Haiku handles classification. Running them in parallel keeps response time clean.

**Signal-based memory** — not every interaction gets stored. The classifier evaluates whether an exchange is significant before writing to long-term memory. This keeps the memory file lean and relevant.

**Async classification** — the background classifier runs in a separate thread after the response is already delivered to the user. Zero added latency.

---

## Built by

Antonio R — [github.com/Tyrunt-A](https://github.com/Tyrunt-A)
