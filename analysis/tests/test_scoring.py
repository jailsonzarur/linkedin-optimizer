from django.test import SimpleTestCase

from analysis.services.scoring import ScorePalette


class ScorePaletteTests(SimpleTestCase):
    def test_missing_score_is_neutral(self):
        self.assertEqual(ScorePalette.tone(None), ScorePalette.NEUTRAL)

    def test_boundaries(self):
        self.assertEqual(ScorePalette.tone(0), ScorePalette.DANGER)
        self.assertEqual(ScorePalette.tone(49), ScorePalette.DANGER)
        self.assertEqual(ScorePalette.tone(50), ScorePalette.WARN)
        self.assertEqual(ScorePalette.tone(74), ScorePalette.WARN)
        self.assertEqual(ScorePalette.tone(75), ScorePalette.ACCENT)
        self.assertEqual(ScorePalette.tone(100), ScorePalette.ACCENT)
