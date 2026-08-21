from django.contrib import admin

from .models import KnowledgeChunk, KnowledgeSource

admin.site.register(KnowledgeSource)
admin.site.register(KnowledgeChunk)
