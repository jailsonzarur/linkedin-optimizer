from django.urls import path

from knowledge.views import (
    conversation_answer_audio,
    conversation_detail,
    conversation_finish,
    conversation_reply,
    conversation_stream,
    message_status,
    import_clear,
    import_detail,
    onboarding_create,
    onboarding_progress,
    onboarding_result,
    onboarding_start,
    onboarding_stream,
)

app_name = "knowledge"

urlpatterns = [
    path("knowledge/", import_detail, name="import_detail"),
    path("knowledge/clear/", import_clear, name="import_clear"),
    path("onboarding/", onboarding_start, name="onboarding_start"),
    path("onboarding/import/", onboarding_create, name="onboarding_create"),
    path("onboarding/<int:pk>/", onboarding_progress, name="onboarding_progress"),
    path("onboarding/<int:pk>/stream/", onboarding_stream, name="onboarding_stream"),
    path("onboarding/<int:pk>/result/", onboarding_result, name="onboarding_result"),
    path("conversation/<int:pk>/", conversation_detail, name="conversation"),
    path("conversation/<int:pk>/reply/", conversation_reply, name="conversation_reply"),
    path("conversation/<int:pk>/stream/", conversation_stream, name="conversation_stream"),
    path("conversation/<int:pk>/audio/", conversation_answer_audio, name="conversation_audio"),
    path("message/<int:pk>/status/", message_status, name="message_status"),
    path("conversation/<int:pk>/finish/", conversation_finish, name="conversation_finish"),
]
