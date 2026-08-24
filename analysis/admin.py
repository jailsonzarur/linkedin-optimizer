from django.contrib import admin

from .models import Analysis, AnalysisBullet, AnalysisSection


class AnalysisBulletInline(admin.TabularInline):
    model = AnalysisBullet
    extra = 0


@admin.register(AnalysisSection)
class AnalysisSectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "analysis", "source_ref")
    list_filter = ("section",)
    inlines = [AnalysisBulletInline]


admin.site.register(Analysis)
