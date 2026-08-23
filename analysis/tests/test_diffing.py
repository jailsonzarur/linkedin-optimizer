from django.test import SimpleTestCase

from analysis.services.diffing import InlineDiffer


class InlineDifferTests(SimpleTestCase):
    def test_identical_text_produces_no_marks(self):
        left, right = InlineDiffer("same sentence", "same sentence").render()
        self.assertNotIn("<span", left)
        self.assertNotIn("<span", right)

    def test_replacement_marks_both_sides(self):
        left, right = InlineDiffer(
            "Developer at TechCorp", "Engineer at TechCorp"
        ).render()
        self.assertIn('<span class="del">Developer</span>', left)
        self.assertIn('<span class="ins">Engineer</span>', right)
        self.assertIn("at TechCorp", left)
        self.assertIn("at TechCorp", right)

    def test_insertion_only_touches_the_suggested_side(self):
        left, right = InlineDiffer("REST APIs", "REST APIs in Django").render()
        self.assertNotIn("<span", left)
        self.assertIn('<span class="ins">in Django</span>', right)

    def test_html_in_the_source_is_escaped(self):
        left, right = InlineDiffer("<script>alert(1)</script>", "safe text").render()
        self.assertNotIn("<script>", left)
        self.assertIn("&lt;script&gt;", left)
        self.assertIn("safe text", right)

    def test_empty_original_yields_pure_insertion(self):
        left, right = InlineDiffer("", "new content").render()
        self.assertEqual(left, "")
        self.assertIn('<span class="ins">new content</span>', right)
