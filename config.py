"""
Recall — Configuration
"""

# ─── Models ───────────────────────────────────────────────────────────────────
MODEL          = "claude-sonnet-4-6"
MODEL_HAIKU    = "claude-haiku-4-5-20251001"
MAX_TOKENS     = 600
TEMPERATURE    = 0.85

# ─── Memory ───────────────────────────────────────────────────────────────────
MEMORY_FILE    = "data/memoria.json"
MAX_HISTORIAL  = 10
MAX_LONG_TERM  = 500

# ─── Behavioral tags ──────────────────────────────────────────────────────────
TAGS = {
    "analytical":    "Analyzes before acting. Looks for patterns and causes.",
    "explorer":      "Acts out of curiosity. Starts things without knowing the end.",
    "cautious":      "Evaluates emotional impact. Blocks clean exits.",
    "focused":       "Protects projects and energy. Closes open loops.",
    "undecided":     "Appears when explorer and cautious conflict.",
    "calculated":    "Acts deliberately in grey areas. Evaluates risk before moving.",
}
