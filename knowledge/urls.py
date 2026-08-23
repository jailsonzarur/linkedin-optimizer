from django.urls import path

from knowledge.views import (
    import_clear,
    import_list,
    onboarding_create,
    onboarding_progress,
    onboarding_result,
    onboarding_start,
    onboarding_stream,
)

app_name = "knowledge"

urlpatterns = [
    path("knowledge/", import_list, name="import_list"),
    path("knowledge/clear/", import_clear, name="import_clear"),
    path("onboarding/", onboarding_start, name="onboarding_start"),
    path("onboarding/import/", onboarding_create, name="onboarding_create"),
    path("onboarding/<int:pk>/", onboarding_progress, name="onboarding_progress"),
    path("onboarding/<int:pk>/stream/", onboarding_stream, name="onboarding_stream"),
    path("onboarding/<int:pk>/result/", onboarding_result, name="onboarding_result"),
]
