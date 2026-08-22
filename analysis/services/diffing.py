import difflib

from django.utils.html import escape
from django.utils.safestring import mark_safe


class InlineDiffer:
    DELETED_CLASS = "del"
    INSERTED_CLASS = "ins"

    def __init__(self, original, suggested):
        self.original = original
        self.suggested = suggested

    def render(self):
        original_words = self.original.split()
        suggested_words = self.suggested.split()
        matcher = difflib.SequenceMatcher(
            None, original_words, suggested_words, autojunk=False
        )

        left, right = [], []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                left.append(self._wrap(original_words[i1:i2]))
                right.append(self._wrap(suggested_words[j1:j2]))
            elif tag == "delete":
                left.append(self._wrap(original_words[i1:i2], self.DELETED_CLASS))
            elif tag == "insert":
                right.append(self._wrap(suggested_words[j1:j2], self.INSERTED_CLASS))
            elif tag == "replace":
                left.append(self._wrap(original_words[i1:i2], self.DELETED_CLASS))
                right.append(self._wrap(suggested_words[j1:j2], self.INSERTED_CLASS))

        return self._join(left), self._join(right)

    @staticmethod
    def _wrap(words, css_class=None):
        if not words:
            return ""
        text = escape(" ".join(words))
        return f'<span class="{css_class}">{text}</span>' if css_class else text

    @staticmethod
    def _join(parts):
        return mark_safe(" ".join(part for part in parts if part))
