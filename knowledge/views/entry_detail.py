from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from knowledge.models import KnowledgeEntry, KnowledgeSource
from knowledge.selectors.detail import KnowledgeEntryDetailSelector
from knowledge.tasks import process_entry


def _selector(user, pk):
    try:
        return KnowledgeEntryDetailSelector.for_user(user, pk)
    except KnowledgeEntry.DoesNotExist as exc:
        raise Http404("Entry not found.") from exc


@login_required
def entry_detail(request, pk):
    return render(request, "knowledge/entry_detail.html", _selector(request.user, pk).context())


@login_required
def entry_detail_body(request, pk):
    """The polling target: everything on the page that changes as work finishes."""
    return render(
        request, "knowledge/partials/_detail_body.html", _selector(request.user, pk).context()
    )


@login_required
@require_POST
def source_update(request, pk):
    source = get_object_or_404(KnowledgeSource, pk=pk, entry__user=request.user)

    source.content = request.POST.get("content", "").strip()
    source.save(update_fields=["content", "updated_at"])

    entry_id = source.entry_id
    KnowledgeEntry.objects.filter(pk=entry_id).update(status=KnowledgeEntry.Status.PENDING)
    transaction.on_commit(lambda: process_entry.delay(entry_id))

    return redirect("knowledge:detail", pk=entry_id)
