from django.contrib.auth import get_user_model
from django.test import TestCase

from analysis.models import Analysis, AnalysisSection, ProfileSnapshot
from analysis.selectors.result import AnalysisResultSelector


class AnalysisResultSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(username="tester")
        snapshot = ProfileSnapshot.objects.create(user=user, raw_content="perfil")
        cls.analysis = Analysis.objects.create(
            user=user,
            profile_snapshot=snapshot,
            overall_score=68,
            overall_score_per_section={"headline": 45, "about": 72, "keywords": 38},
            keyword_gap=[
                {"term": "Docker", "coverage": 87, "present": False, "supported": True},
                {"term": "Kubernetes", "coverage": 51, "present": False, "supported": False},
                {"term": "PostgreSQL", "coverage": 68, "present": True, "supported": True},
            ],
        )
        AnalysisSection.objects.create(
            analysis=cls.analysis,
            section=AnalysisSection.Section.HEADLINE,
            original_text="Desenvolvedor",
            suggested_text="Backend Developer",
            variant_index=0,
        )
        AnalysisSection.objects.create(
            analysis=cls.analysis,
            section=AnalysisSection.Section.HEADLINE,
            original_text="Desenvolvedor",
            suggested_text="Engenheiro Backend",
            variant_index=1,
        )
        AnalysisSection.objects.create(
            analysis=cls.analysis,
            section=AnalysisSection.Section.ABOUT,
            original_text="texto igual",
            suggested_text="texto igual",
            variant_index=0,
        )

    def selector(self):
        return AnalysisResultSelector.for_pk(self.analysis.pk)

    def test_only_primary_variant_becomes_a_row(self):
        groups = {group["key"]: group for group in self.selector().groups()}
        self.assertEqual(groups["headline"]["total"], 1)
        self.assertEqual(groups["headline"]["alternates"], 1)

    def test_unchanged_section_is_not_counted_as_changed(self):
        groups = {group["key"]: group for group in self.selector().groups()}
        self.assertEqual(groups["about"]["changed_count"], 0)
        self.assertFalse(groups["about"]["rows"][0]["changed"])

    def test_only_unsupported_missing_terms_are_flagged(self):
        context = self.selector().context()
        self.assertEqual(context["unsupported_terms"], "Kubernetes")
        self.assertEqual(context["keyword_missing_count"], 2)

    def test_section_without_rows_is_omitted(self):
        keys = [group["key"] for group in self.selector().groups()]
        self.assertNotIn("experience_bullet", keys)

    def test_sections_are_fetched_once(self):
        selector = self.selector()
        with self.assertNumQueries(0):
            selector.groups()
            selector.groups()

    def test_missing_analysis_raises(self):
        with self.assertRaises(Analysis.DoesNotExist):
            AnalysisResultSelector.for_pk(99999)
