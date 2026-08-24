from django.db import transaction

from analysis.models import Analysis
from analysis.tasks import analyse_profile
from knowledge.models import Conversation


def finalise(conversation):
    conversation.status = Conversation.Status.COMPLETED
    conversation.save(update_fields=["status", "updated_at"])

    analysis, _ = Analysis.objects.get_or_create(
        user=conversation.user,
        profile_import=conversation.profile_import,
        defaults={"status": Analysis.Status.PENDING},
    )
    analysis.status = Analysis.Status.PENDING
    analysis.save(update_fields=["status"])

    transaction.on_commit(lambda: analyse_profile.delay(analysis.pk))
    return analysis
