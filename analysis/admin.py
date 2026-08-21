from django.contrib import admin

from .models import Analysis, AnalysisSection, ProfileSnapshot

admin.site.register(ProfileSnapshot)
admin.site.register(Analysis)
admin.site.register(AnalysisSection)
