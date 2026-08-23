from django.test import SimpleTestCase

from knowledge.services.chunker import Chunker


class ChunkerBatchingTests(SimpleTestCase):
    def test_short_contents_stay_in_one_call(self):
        chunker = Chunker(client=object(), char_limit=100)
        self.assertEqual(chunker.batches(["abc", "def"]), [["abc", "def"]])

    def test_contents_are_split_once_they_pass_the_limit(self):
        chunker = Chunker(client=object(), char_limit=10)
        batches = chunker.batches(["a" * 8, "b" * 8, "c" * 8])
        self.assertEqual([len(batch) for batch in batches], [1, 1, 1])

    def test_blank_contents_are_dropped(self):
        chunker = Chunker(client=object(), char_limit=100)
        self.assertEqual(chunker.batches(["  ", "", "real"]), [["real"]])

    def test_no_content_means_no_calls(self):
        chunker = Chunker(client=object(), char_limit=100)
        self.assertEqual(chunker.batches([]), [])
