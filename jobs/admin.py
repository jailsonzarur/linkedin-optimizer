from django.contrib import admin

from .models import JobPosting, TargetRoleCatalog

admin.site.register(TargetRoleCatalog)
admin.site.register(JobPosting)
