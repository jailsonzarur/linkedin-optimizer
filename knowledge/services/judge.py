import json

from django.conf import settings

from knowledge.prompts.judge import (
    JUDGE_EXPERIENCE_SYSTEM_PROMPT,
    JUDGE_SECTIONS_SYSTEM_PROMPT,
    PARSE_SYSTEM_PROMPT,
)
from knowledge.services.openai_client import get_client


class ProfileJudge:
    SEED = 11


    def __init__(self, client=None, model=None, on_event=None):
        self._client = client
        self.model = model or settings.OPENAI_EXTRACTION_MODEL
        self.on_event = on_event or (lambda name, detail: None)

    @property
    def client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def _ask(self, system, user):
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0,
            seed=self.SEED,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        try:
            return json.loads(response.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _document(profile_text, resume_text):
        parts = [f"=== LINKEDIN PROFILE (this is what recruiters see) ===\n{profile_text}"]
        if resume_text:
            parts.append(
                "=== RÉSUMÉ (not published — anything here that is missing from the "
                f"profile above is itself a finding) ===\n{resume_text}"
            )
        return "\n\n".join(parts)

    def run(self, profile_text, resume_text=""):
        raw_text = self._document(profile_text, resume_text)
        parsed = self._ask(PARSE_SYSTEM_PROMPT, raw_text)
        experiences = parsed.get("experiences") or []
        self.on_event("judge.parsed", len(experiences))

        for index, experience in enumerate(experiences, start=1):
            self.on_event("judge.progress", f"{index}/{len(experiences)}|{experience.get('company','')}")
            verdict = self._ask(
                JUDGE_EXPERIENCE_SYSTEM_PROMPT,
                f"FULL PROFILE:\n{raw_text}\n\nJUDGE THIS EXPERIENCE:\n"
                f"{json.dumps(experience, ensure_ascii=False)}",
            )
            experience["judgments"] = [
                {"kind": check.get("kind") or "weak",
                 "note": check.get("note", ""),
                 "quote": check.get("quote", ""),
                 "check": check.get("id", "")}
                for check in verdict.get("checks") or []
                if check.get("verdict") == "fail"
            ]
            experience["learned"] = []

        self.on_event("judge.sections", "")
        sections = self._ask(
            JUDGE_SECTIONS_SYSTEM_PROMPT,
            f"FULL PROFILE:\n{raw_text}\n\nSTRUCTURE:\n"
            f"{json.dumps(parsed, ensure_ascii=False)}",
        )

        failed = [c for c in sections.get("checks") or [] if c.get("verdict") == "fail"]

        def judgments_for(prefix):
            return [
                {"kind": c.get("kind") or "weak", "note": c.get("note", ""),
                 "quote": c.get("quote", ""), "check": c.get("id", "")}
                for c in failed
                if str(c.get("id", "")).startswith(prefix)
            ]

        record = {
            "experiences": experiences,
            "headline": {**(parsed.get("headline") or {}),
                         "judgments": judgments_for("headline"), "learned": []},
            "about": {**(parsed.get("about") or {}),
                      "judgments": judgments_for("about"), "learned": []},
            "skills": {**(parsed.get("skills") or {}),
                       "backed_by": sections.get("backed_by") or {},
                       "judgments": judgments_for("skills"), "learned": []},
            "target": {"role": "", "work_mode": "", "notes": ""},
        }
        total = sum(len(e.get("judgments") or []) for e in experiences) + len(failed)
        self.on_event("judge.done", total)
        return record
