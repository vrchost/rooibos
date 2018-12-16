from __future__ import absolute_import
from django.contrib import admin
from .models import Impersonation


class ImpersonationAdmin(admin.ModelAdmin):
    filter_horizontal = ('users', 'groups')


admin.site.register(Impersonation, ImpersonationAdmin)
