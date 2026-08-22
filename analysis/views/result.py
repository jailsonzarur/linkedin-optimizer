from django.http import Http404
from django.shortcuts import render

from analysis.models import Analysis
from analysis.selectors.result import AnalysisResultSelector


def analysis_result(request, pk):
    try:
        selector = AnalysisResultSelector.for_pk(pk)
    except Analysis.DoesNotExist as exc:
        raise Http404("Analysis not found.") from exc

    return render(request, "analysis/result.html", selector.context())
