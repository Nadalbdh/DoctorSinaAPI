from django.contrib import admin

from emails.models import Email
from settings.admin import ExportModelAdmin


class EmailAdmin(ExportModelAdmin):
    list_display = ["email", "municipality"]


admin.site.register(Email, EmailAdmin)
