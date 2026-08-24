import json

from django.conf import settings

from knowledge.prompts.extractor import EXTRACTOR_SYSTEM_PROMPT
from knowledge.prompts.interviewer import (
    INTERVIEWER_OPENING_PROMPT,
    INTERVIEWER_SYSTEM_PROMPT,
)
from knowledge.services.openai_client import get_async_client, get_client

HISTORY_TURNS = 12


def transcript(messages):
    return [{"role": m.role, "content": m.content} for m in messages if m.content]


def _interviewer_context(record):
    return (
        f"RECORD:\n{json.dumps(record, ensure_ascii=False)}\n\nInterface locale: pt-BR."
    )


def opening_question(record):
    response = get_client().chat.completions.create(
        model=settings.OPENAI_EXTRACTION_MODEL,
        messages=[
            {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
            {"role": "system", "content": _interviewer_context(record)},
            {"role": "user", "content": INTERVIEWER_OPENING_PROMPT},
        ],
    )
    return (response.choices[0].message.content or "").strip()


async def extract(record, messages):
    client = get_async_client()
    exchange = "\n".join(f"{m['role']}: {m['content']}" for m in transcript(messages)[-4:])
    response = await client.chat.completions.create(
        model=settings.OPENAI_EXTRACTION_MODEL,
        response_format={"type": "json_object"},
        temperature=0,
        seed=11,
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"RECORD:\n{json.dumps(record, ensure_ascii=False)}\n\n"
                f"LAST EXCHANGE:\n{exchange}",
            },
        ],
    )
    try:
        return json.loads(response.choices[0].message.content or "{}") or record
    except json.JSONDecodeError:
        return record


async def stream_question(record, messages):
    client = get_async_client()
    stream = await client.chat.completions.create(
        model=settings.OPENAI_EXTRACTION_MODEL,
        stream=True,
        messages=[
            {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
            {"role": "system", "content": _interviewer_context(record)},
            *transcript(messages)[-HISTORY_TURNS:],
        ],
    )
    async for chunk in stream:
        token = chunk.choices[0].delta.content if chunk.choices else None
        if token:
            yield token


CLOSING_MARKER = "[READY_TO_CLOSE]"


def split_closing(text):
    if CLOSING_MARKER in text:
        return text.replace(CLOSING_MARKER, "").strip(), True
    return text, False
