from django.urls import path

from . import views

app_name = "analysis"

urlpatterns = [
    path("analysis/<int:pk>/", views.analysis_result, name="result"),
]
