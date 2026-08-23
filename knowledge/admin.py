from django.contrib import admin

from .models import Conversation, Message, ProfileImport


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0


@admin.register(ProfileImport)
class ProfileImportAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "status", "created_at")
    list_filter = ("status",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "status", "created_at")
    list_filter = ("status",)
    inlines = [MessageInline]
