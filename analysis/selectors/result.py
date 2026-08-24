from analysis.models import Analysis, AnalysisBullet, AnalysisSection
from analysis.services.diffing import InlineDiffer
from analysis.services.scoring import ScorePalette


class AnalysisResultSelector:
    SECTION_ORDER = [
        (AnalysisSection.Section.HEADLINE, "Headline"),
        (AnalysisSection.Section.ABOUT, "About"),
        (AnalysisSection.Section.EXPERIENCE_BULLET, "Experience"),
    ]
    PRIMARY_VARIANT = 0

    def __init__(self, analysis):
        self.analysis = analysis
        self.sections = list(analysis.sections.all())

    @classmethod
    def for_user(cls, user, pk):
        analysis = (
            Analysis.objects.select_related("user")
            .prefetch_related("sections__bullets")
            .get(pk=pk, user=user)
        )
        return cls(analysis)

    def context(self):
        keyword_rows = self.keyword_rows()
        missing = [row for row in keyword_rows if not row["present"]]
        unsupported = [row["term"] for row in missing if not row["supported"]]

        return {
            "analysis": self.analysis,
            "groups": self.groups(),
            "section_scores": self.section_scores(),
            "overall_tone": ScorePalette.tone(self.analysis.overall_score),
            "keyword_rows": keyword_rows,
            "keyword_missing_count": len(missing),
            "unsupported_terms": self._humanize(unsupported),
        }

    def groups(self):
        groups = []
        for key, label in self.SECTION_ORDER:
            if key == AnalysisSection.Section.EXPERIENCE_BULLET:
                groups += self._experience_groups()
                continue

            rows = self._rows_for(key)
            if not rows:
                continue

            changed_count = sum(1 for row in rows if row["changed"])
            groups.append({
                "key": key,
                "label": label,
                "rows": rows,
                "bullets": None,
                "changed_count": changed_count,
                "changed_summary": f"{changed_count} of {len(rows)} changed",
                "total": len(rows),
                "alternates": self._alternates_for(key),
                "tone": ScorePalette.tone(self.analysis.overall_score_per_section.get(key)),
            })
        return groups

    def _experience_groups(self):
        groups = []
        for section in self.sections:
            if section.section != AnalysisSection.Section.EXPERIENCE_BULLET:
                continue

            bullets = list(section.bullets.all())
            originals = [b for b in bullets if b.kind == AnalysisBullet.Kind.ORIGINAL]
            suggested = [b for b in bullets if b.kind == AnalysisBullet.Kind.SUGGESTED]
            if not originals and not suggested:
                continue

            rendered = []
            for bullet in suggested:
                text = bullet.text
                is_new = text.startswith("[new] ")
                rendered.append({"text": text.removeprefix("[new] "), "is_new": is_new})

            groups.append({
                "key": f"{AnalysisSection.Section.EXPERIENCE_BULLET}:{section.source_ref}",
                "label": self._experience_label(section.source_ref),
                "rows": None,
                "bullets": {"original": originals, "suggested": rendered},
                "changed_count": sum(1 for b in rendered if b["is_new"]),
                "changed_summary": f"{sum(1 for b in rendered if b['is_new'])} new",
                "total": len(rendered),
                "alternates": 0,
                "tone": ScorePalette.tone(
                    self.analysis.overall_score_per_section.get("experience_bullet")
                ),
            })
        return groups

    def _experience_label(self, source_ref):
        record = (self.analysis.profile_import.conversations.first() or None)
        experiences = ((record.record if record else self.analysis.profile_import.judgment)
                       or {}).get("experiences") or []
        for experience in experiences:
            if experience.get("id") == source_ref:
                company = experience.get("company") or ""
                title = experience.get("title") or ""
                return f"{company} · {title}".strip(" ·") or "Experience"
        return "Experience"

    def section_scores(self):
        per_section = self.analysis.overall_score_per_section
        scores = [
            {
                "label": label,
                "value": per_section.get(key, 0),
                "tone": ScorePalette.tone(per_section.get(key)),
            }
            for key, label in self.SECTION_ORDER
        ]

        keywords = per_section.get("keywords")
        if keywords is not None:
            scores.append(
                {
                    "label": "Keywords",
                    "value": keywords,
                    "tone": ScorePalette.tone(keywords),
                }
            )
        return scores

    def keyword_rows(self):
        rows = []
        for entry in self.analysis.keyword_gap:
            coverage = entry.get("coverage", 0)
            present = entry.get("present", False)
            rows.append(
                {
                    "term": entry.get("term", ""),
                    "coverage": coverage,
                    "present": present,
                    "supported": entry.get("supported", False),
                    "tone": ScorePalette.ACCENT if present else ScorePalette.DANGER,
                    "note": f"{coverage}% of jobs · {'present' if present else 'missing'}",
                }
            )
        return rows

    def _rows_for(self, key):
        rows = []
        for section in self.sections:
            if section.section != key or section.variant_index != self.PRIMARY_VARIANT:
                continue

            left, right = InlineDiffer(section.original_text, section.suggested_text).render()
            rows.append(
                {
                    "left": left,
                    "right": right,
                    "changed": section.original_text.strip() != section.suggested_text.strip(),
                    "suggested": section.suggested_text,
                }
            )
        return rows

    def _alternates_for(self, key):
        return sum(
            1
            for section in self.sections
            if section.section == key and section.variant_index > self.PRIMARY_VARIANT
        )

    @staticmethod
    def _humanize(items):
        items = list(items)
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return f"{', '.join(items[:-1])} and {items[-1]}"
