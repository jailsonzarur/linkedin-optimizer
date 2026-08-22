from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from analysis.models import Analysis


@login_required
def home(request):
    latest = Analysis.objects.filter(user=request.user).first()
    return render(request, "accounts/home.html", {"latest_analysis": latest})
