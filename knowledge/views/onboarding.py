from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from knowledge.models import ProfileImport
from knowledge.tasks import extract_import

MAX_PDF_BYTES = 10 * 1024 * 1024


def onboarding_done(user):
    return user.conversations.filter(status="completed").exists()


def current_import(user):
    return ProfileImport.objects.filter(user=user).first()


@login_required
def onboarding_start(request):
    existing = current_import(request.user)
    if existing and existing.status != ProfileImport.Status.FAILED:
        return redirect("knowledge:onboarding_progress", pk=existing.pk)
    return render(request, "knowledge/onboarding_start.html")


def _check(upload, label, required):
    if not upload:
        return f"{label} is required." if required else None
    if not upload.name.lower().endswith(".pdf"):
        return f"{label} must be a PDF."
    if upload.size > MAX_PDF_BYTES:
        return f"{label} is over 10 MB."
    return None


@login_required
@require_POST
def onboarding_create(request):
    linkedin_pdf = request.FILES.get("linkedin_pdf")
    resume = request.FILES.get("resume")

    errors = [
        message
        for message in (
            _check(linkedin_pdf, "Your LinkedIn PDF", required=True),
            _check(resume, "Your résumé", required=False),
        )
        if message
    ]
    if errors:
        return render(request, "knowledge/onboarding_start.html", {"errors": errors}, status=400)

    ProfileImport.objects.filter(user=request.user).delete()
    profile_import = ProfileImport.objects.create(
        user=request.user, linkedin_pdf=linkedin_pdf, resume=resume or None
    )
    transaction.on_commit(lambda: extract_import.delay(profile_import.pk))
    return redirect("knowledge:onboarding_progress", pk=profile_import.pk)


@login_required
def onboarding_progress(request, pk):
    profile_import = get_object_or_404(ProfileImport, pk=pk, user=request.user)
    if profile_import.status == ProfileImport.Status.READY:
        return redirect("knowledge:onboarding_result", pk=pk)
    return render(request, "knowledge/onboarding_progress.html", {"import": profile_import})


@login_required
def onboarding_result(request, pk):
    profile_import = get_object_or_404(ProfileImport, pk=pk, user=request.user)
    record = profile_import.judgment or {}
    conversation = profile_import.conversations.first()
    sections = [
        {"name": name, "data": record.get(name) or {}}
        for name in ("headline", "about", "skills")
    ]
    total = sum(len(e.get("judgments") or []) for e in record.get("experiences") or [])
    total += sum(len(s["data"].get("judgments") or []) for s in sections)
    return render(request, "knowledge/onboarding_result.html", {
        "import": profile_import,
        "conversation": conversation,
        "experiences": record.get("experiences") or [],
        "sections": sections,
        "unbacked": [k for k, v in ((record.get("skills") or {}).get("backed_by") or {}).items() if not v],
        "total": total,
    })


@login_required
def import_detail(request):
    existing = current_import(request.user)
    if not existing:
        return redirect("knowledge:onboarding_start")
    if existing.status != ProfileImport.Status.READY:
        return redirect("knowledge:onboarding_progress", pk=existing.pk)
    return redirect("knowledge:onboarding_result", pk=existing.pk)


@login_required
@require_POST
def import_clear(request):
    ProfileImport.objects.filter(user=request.user).delete()
    return redirect("knowledge:onboarding_start")
