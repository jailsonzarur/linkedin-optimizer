from django.urls import path

from knowledge.views import entry_create, entry_list

app_name = "knowledge"

urlpatterns = [
    path("knowledge/", entry_list, name="list"),
    path("knowledge/new/", entry_create, name="create"),
]
