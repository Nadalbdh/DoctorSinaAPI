from django.contrib.admin import ModelAdmin
from import_export.admin import ExportActionMixin


class ExportModelAdmin(ExportActionMixin, ModelAdmin):
    pass
