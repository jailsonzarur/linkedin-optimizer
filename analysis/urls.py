from django.urls import path

from analysis.views import analysis_result, analysis_running, analysis_stream

app_name = "analysis"

urlpatterns = [
    path("analysis/<int:pk>/", analysis_result, name="result"),
    path("analysis/<int:pk>/running/", analysis_running, name="running"),
    path("analysis/<int:pk>/stream/", analysis_stream, name="stream"),
]
