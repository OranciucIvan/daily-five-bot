import json
from ollama_client import chat


def weekly_summary(entries: list[tuple[str, str, int]]) -> str:
    if not entries:
        return "No entries this week yet."
    try:
        payload = [{"role": "system", "content": (
            "You are a gentle weekly reviewer. Analyze the entries: main topics mentioned, overall tone, "
            "and one encouraging observation. No medical advice. If many days are refused or empty, say so kindly. "
            "Keep it under 120 words."
        )}, {"role": "user", "content": json.dumps(entries, ensure_ascii=False)}]
        reply = chat(payload)
        return reply or fallback_summary(entries)
    except Exception:
        return fallback_summary(entries)


def fallback_summary(entries: list[tuple[str, str, int]]) -> str:
    skipped = sum(1 for _, _, s in entries if s)
    filled = len(entries) - skipped
    return f"This week: {filled} day(s) with entries, {skipped} refused/skipped. Keep noticing the good things."
