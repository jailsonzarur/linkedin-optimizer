from django.db.models import Count, Q

from knowledge.models import KnowledgeEntry, KnowledgeSource


class KnowledgeEntryListSelector:
    def __init__(self, user):
        self.user = user

    def entries(self):
        return (
            KnowledgeEntry.objects.filter(user=self.user)
            .annotate(
                text_count=Count("sources", filter=Q(sources__type=KnowledgeSource.SourceType.TEXT)),
                audio_count=Count("sources", filter=Q(sources__type=KnowledgeSource.SourceType.AUDIO)),
            )
            .prefetch_related("sources")
        )

    def summary(self):
        entries = list(self.entries())
        return {
            "entries": entries,
            "total": len(entries),
            "pending": sum(1 for e in entries if e.status != KnowledgeEntry.Status.READY),
        }
