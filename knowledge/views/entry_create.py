from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from knowledge.services.entry_builder import KnowledgeEntryBuilder


@login_required
def entry_create(request):
    if request.method != "POST":
        return render(request, "knowledge/entry_form.html")

    builder = KnowledgeEntryBuilder(request.user, request.POST.get("title", ""))

    for content in request.POST.getlist("text_content"):
        builder.add_text(content)

    for uploaded in request.FILES.getlist("audio_files"):
        builder.add_audio(uploaded)

    if not builder.is_valid():
        return render(
            request,
            "knowledge/entry_form.html",
            {"errors": builder.errors, "title": request.POST.get("title", "")},
            status=400,
        )

    builder.save()
    return redirect("knowledge:list")
