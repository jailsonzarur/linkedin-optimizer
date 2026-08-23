from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from analysis.models import Analysis
from knowledge.models import ProfileImport
from knowledge.views.onboarding import onboarding_done


@login_required
def home(request):
    latest = Analysis.objects.filter(user=request.user).first()
    pending_import = (
        ProfileImport.objects.filter(user=request.user)
        .exclude(status=ProfileImport.Status.FAILED)
        .first()
    )
    return render(request, "accounts/home.html", {
        "latest_analysis": latest,
        "onboarding_done": onboarding_done(request.user),
        "pending_import": pending_import,
    })
