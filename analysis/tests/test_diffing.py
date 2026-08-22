from django.test import SimpleTestCase

from analysis.services.diffing import InlineDiffer


class InlineDifferTests(SimpleTestCase):
    def test_identical_text_produces_no_marks(self):
        left, right = InlineDiffer("mesma frase", "mesma frase").render()
        self.assertNotIn("<span", left)
        self.assertNotIn("<span", right)

    def test_replacement_marks_both_sides(self):
        left, right = InlineDiffer(
            "Desenvolvedor na TechCorp", "Backend Developer na TechCorp"
        ).render()
        self.assertIn('<span class="del">Desenvolvedor</span>', left)
        self.assertIn('<span class="ins">Backend Developer</span>', right)
        self.assertIn("na TechCorp", left)
        self.assertIn("na TechCorp", right)

    def test_insertion_only_touches_the_suggested_side(self):
        left, right = InlineDiffer("APIs REST", "APIs REST em Django").render()
        self.assertNotIn("<span", left)
        self.assertIn('<span class="ins">em Django</span>', right)

    def test_html_in_the_source_is_escaped(self):
        left, right = InlineDiffer("<script>alert(1)</script>", "texto seguro").render()
        self.assertNotIn("<script>", left)
        self.assertIn("&lt;script&gt;", left)
        self.assertIn("texto seguro", right)

    def test_empty_original_yields_pure_insertion(self):
        left, right = InlineDiffer("", "conteúdo novo").render()
        self.assertEqual(left, "")
        self.assertIn('<span class="ins">conteúdo novo</span>', right)
