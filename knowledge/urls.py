from django.urls import path

from knowledge.views import (
    entry_create,
    entry_detail,
    entry_detail_body,
    entry_list,
    entry_list_body,
    source_update,
)

app_name = "knowledge"

urlpatterns = [
    path("knowledge/", entry_list, name="list"),
    path("knowledge/body/", entry_list_body, name="list_body"),
    path("knowledge/new/", entry_create, name="create"),
    path("knowledge/<int:pk>/", entry_detail, name="detail"),
    path("knowledge/<int:pk>/body/", entry_detail_body, name="detail_body"),
    path("knowledge/source/<int:pk>/", source_update, name="source_update"),
]
