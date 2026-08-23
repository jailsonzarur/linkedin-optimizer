from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from knowledge.selectors.entries import KnowledgeEntryListSelector


@login_required
def entry_list(request):
    selector = KnowledgeEntryListSelector(request.user)
    return render(request, "knowledge/entry_list.html", selector.summary())


@login_required
def entry_list_body(request):
    """The polling target: the same block the full page renders."""
    selector = KnowledgeEntryListSelector(request.user)
    return render(request, "knowledge/partials/_list_body.html", selector.summary())
