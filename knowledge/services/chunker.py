import json

from django.conf import settings

from knowledge.models import KnowledgeChunk
from knowledge.services.openai_client import get_client

SYSTEM_PROMPT = """You extract factual claims about a person's career from their own words.

Return JSON: {"chunks": [{"content": ..., "category": ...}]}

Rules:
- category is one of: experience, skill, achievement, education, other
- Each chunk is one self-contained claim, readable without the surrounding text.
- Merge repeated statements. The same fact told twice is one chunk.
- Preserve concrete details: technologies, numbers, company names, dates.
- Never invent, embellish or infer beyond what was said.
- Write chunks in the same language the person used.
- Skip filler that says nothing about their career."""


class Chunker:
    VALID_CATEGORIES = {choice.value for choice in KnowledgeChunk.Category}

    def __init__(self, client=None, model=None, char_limit=None):
        self._client = client
        self.model = model or settings.OPENAI_EXTRACTION_MODEL
        self.char_limit = char_limit or settings.KNOWLEDGE_EXTRACTION_CHAR_LIMIT

    @property
    def client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def batches(self, contents):
        """Group source contents so no single extraction call runs past the limit."""
        batches, current, size = [], [], 0

        for content in contents:
            content = (content or "").strip()
            if not content:
                continue
            if current and size + len(content) > self.char_limit:
                batches.append(current)
                current, size = [], 0
            current.append(content)
            size += len(content)

        if current:
            batches.append(current)
        return batches

    def extract(self, contents):
        chunks = []
        for batch in self.batches(contents):
            chunks.extend(self._extract_one(batch))
        return chunks

    def _extract_one(self, batch):
        joined = "\n\n---\n\n".join(batch)
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": joined},
            ],
        )

        try:
            payload = json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            return []

        extracted = []
        for item in payload.get("chunks", []):
            content = (item.get("content") or "").strip()
            if not content:
                continue
            category = item.get("category")
            if category not in self.VALID_CATEGORIES:
                category = KnowledgeChunk.Category.OTHER
            extracted.append({"content": content, "category": category})
        return extracted
