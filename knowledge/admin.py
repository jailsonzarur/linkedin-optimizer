from django.contrib import admin

from .models import KnowledgeChunk, KnowledgeEntry, KnowledgeSource


class KnowledgeSourceInline(admin.TabularInline):
    model = KnowledgeSource
    extra = 0


@admin.register(KnowledgeEntry)
class KnowledgeEntryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "status", "created_at")
    list_filter = ("status",)
    inlines = [KnowledgeSourceInline]


admin.site.register(KnowledgeSource)
admin.site.register(KnowledgeChunk)
