import asyncio
import re
from groq import Groq
from bot import config

_client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None

MODEL = "llama-3.3-70b-versatile"

# Machine-readable tag the model must append so we can track prediction
# accuracy later. Kept in English regardless of response language so parsing
# doesn't depend on translation.
_PICK_INSTRUCTION = {
    "ru": (
        "\n\nВ самом конце ответа, отдельной строкой, добавь ТОЧНО в таком "
        "формате (без перевода и без изменений) свой прогноз на исход матча: "
        "[PICK: HOME] — если фаворит хозяева, [PICK: DRAW] — если наиболее "
        "вероятна ничья, [PICK: AWAY] — если фаворит гости."
    ),
    "en": (
        "\n\nAt the very end of your answer, on its own line, add EXACTLY "
        "this tag with your match-winner prediction: [PICK: HOME] if the "
        "home team is favored, [PICK: DRAW] if a draw is most likely, "
        "[PICK: AWAY] if the away team is favored."
    ),
}

SYSTEM_PROMPT = {
    "ru": (
        "Ты — профессиональный спортивный аналитик по футбольным ставкам. "
        "Тебе дают статистику по матчу (форма команд, победы/ничьи/поражения, "
        "голы, карточки, очные встречи). На основе ЭТИХ данных дай краткий, "
        "структурированный разбор: какие рынки ставок выглядят статистически "
        "обоснованными (например: тотал, обе забьют, победа/ничья, карточки), "
        "а какие лучше пропустить и почему. Пиши по-русски, кратко, по пунктам, "
        "используй эмодзи для наглядности. Не давай гарантий и не говори "
        "'точно зайдёт' — только вероятностные формулировки на основе статистики."
    ) + _PICK_INSTRUCTION["ru"],
    "en": (
        "You are a professional football betting analyst. You are given match "
        "statistics (team form, wins/draws/losses, goals, cards, head-to-head). "
        "Based ONLY on this data, give a short structured breakdown: which betting "
        "markets look statistically reasonable (e.g. totals, BTTS, "
        "win/draw, cards) and which are better to skip, and why. Write in English, "
        "concise, bullet points, use emojis for clarity. Never guarantee outcomes — "
        "only probabilistic language based on the stats."
    ) + _PICK_INSTRUCTION["en"],
}

_PICK_RE = re.compile(r"\[PICK:\s*(HOME|DRAW|AWAY)\]", re.IGNORECASE)


def extract_pick(text: str) -> str | None:
    """Pulls the model's [PICK: HOME/DRAW/AWAY] tag out as 'home'/'draw'/'away'."""
    match = _PICK_RE.search(text or "")
    return match.group(1).lower() if match else None


def strip_pick_tag(text: str) -> str:
    """Removes the tag from text shown to the user — it's for tracking only."""
    return _PICK_RE.sub("", text or "").rstrip()


def _sync_call(lang: str, stats_text: str) -> str:
    if _client is None:
        return "⚠️ GROQ_API_KEY is not configured."
    completion = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.get(lang, SYSTEM_PROMPT["ru"])},
            {"role": "user", "content": stats_text},
        ],
        temperature=0.4,
        max_tokens=700,
    )
    return completion.choices[0].message.content


async def analyze_match(lang: str, stats_text: str) -> str:
    return await asyncio.to_thread(_sync_call, lang, stats_text)
