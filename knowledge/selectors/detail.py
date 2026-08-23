from knowledge.models import KnowledgeChunk, KnowledgeEntry


class KnowledgeEntryDetailSelector:
    SETTLED = {KnowledgeEntry.Status.READY, KnowledgeEntry.Status.FAILED}

    def __init__(self, entry):
        self.entry = entry

    @classmethod
    def for_user(cls, user, pk):
        entry = (
            KnowledgeEntry.objects.prefetch_related("sources", "chunks").get(pk=pk, user=user)
        )
        return cls(entry)

    def chunk_groups(self):
        grouped = {}
        for chunk in self.entry.chunks.all():
            grouped.setdefault(chunk.category, []).append(chunk)

        return [
            {"category": value, "label": label, "chunks": grouped[value]}
            for value, label in KnowledgeChunk.Category.choices
            if value in grouped
        ]

    def context(self):
        return {
            "entry": self.entry,
            "sources": list(self.entry.sources.all()),
            "chunk_groups": self.chunk_groups(),
            "chunk_count": len(self.entry.chunks.all()),
            "is_processing": self.entry.status not in self.SETTLED,
        }
