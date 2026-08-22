from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from analysis.models import Analysis
from analysis.selectors.result import AnalysisResultSelector


@login_required
def analysis_result(request, pk):
    try:
        selector = AnalysisResultSelector.for_user(request.user, pk)
    except Analysis.DoesNotExist as exc:
        raise Http404("Analysis not found.") from exc

    return render(request, "analysis/result.html", selector.context())
