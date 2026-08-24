import json

from django.conf import settings

from analysis.prompts.rewriter import (
    ABOUT_PROMPT,
    EXPERIENCE_PROMPT,
    HEADLINE_PROMPT,
    SCORING_PROMPT,
)
from knowledge.services.openai_client import get_client


class ProfileRewriter:
    SEED = 11
    WRITING_TEMPERATURE = 0.4

    def __init__(self, record, client=None, model=None, on_event=None):
        self.record = record or {}
        self._client = client
        self.model = model or settings.OPENAI_EXTRACTION_MODEL
        self.on_event = on_event or (lambda name, detail: None)

    @property
    def client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def _language(self):
        for experience in self._experiences():
            for line in experience.get("learned") or []:
                if any(word in line.lower() for word in (" que ", " para ", " com ", " uma ")):
                    return "Portuguese"
        return "English"

    def _ask(self, system, payload, temperature=None):
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=self.WRITING_TEMPERATURE if temperature is None else temperature,
            seed=self.SEED,
            messages=[
                {"role": "system", "content": system},
                {"role": "system", "content": f"Write everything in {self._language()}."},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        try:
            return json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            return {}

    def _section(self, name):
        return self.record.get(name) or {}

    def _experiences(self):
        return self.record.get("experiences") or []

    def headline(self):
        self.on_event("analysis.headline", "")
        section = self._section("headline")
        result = self._ask(HEADLINE_PROMPT, {
            "current": section.get("current", ""),
            "learned": section.get("learned", []),
            "experiences": self._experiences(),
            "skills": self._section("skills"),
            "target": self.record.get("target") or {},
        }, temperature=0.7)
        return section.get("current", ""), (result.get("variants") or [])[:3]

    def about(self):
        self.on_event("analysis.about", "")
        section = self._section("about")
        result = self._ask(ABOUT_PROMPT, {
            "current": section.get("current", ""),
            "learned": section.get("learned", []),
            "experiences": self._experiences(),
            "target": self.record.get("target") or {},
        })
        return section.get("current", ""), result.get("text", "")

    @staticmethod
    def split_bullets(content):
        if not content:
            return []
        text = content.replace("\u2022", "\n").replace(" - ", "\n")
        lines = [line.strip(" -*\u2022\t") for line in text.splitlines()]
        return [line for line in lines if len(line) > 12]

    def experiences(self):
        experiences = self._experiences()
        for index, experience in enumerate(experiences, start=1):
            label = f"{index}/{len(experiences)}|{experience.get('company', '')}"
            self.on_event("analysis.experience", label)
            originals = self.split_bullets(experience.get("content", ""))
            result = self._ask(EXPERIENCE_PROMPT, {
                "title": experience.get("title"),
                "company": experience.get("company"),
                "bullets": originals,
                "learned": experience.get("learned") or [],
                "judgments": experience.get("judgments") or [],
            })
            suggested = [
                b for b in (result.get("bullets") or [])
                if isinstance(b, dict) and b.get("text")
            ]
            yield experience, originals, suggested

    def scores(self):
        self.on_event("analysis.scoring", "")
        result = self._ask(SCORING_PROMPT, {
            "findings": {
                name: self._section(name).get("judgments", [])
                for name in ("headline", "about", "skills")
            },
            "experience_findings": [
                e.get("judgments", []) for e in self._experiences()
            ],
            "headline": self._section("headline").get("current", ""),
            "about": self._section("about").get("current", ""),
            "skills": self._section("skills").get("current", []),
            "experiences": [
                {"title": e.get("title"), "company": e.get("company"), "content": e.get("content")}
                for e in self._experiences()
            ],
        }, temperature=0)
        sections = result.get("sections") or {}
        return result.get("overall"), {k: v for k, v in sections.items() if isinstance(v, int)}
