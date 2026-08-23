from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from knowledge.selectors.entries import KnowledgeEntryListSelector


@login_required
def entry_list(request):
    selector = KnowledgeEntryListSelector(request.user)
    return render(request, "knowledge/entry_list.html", selector.summary())
