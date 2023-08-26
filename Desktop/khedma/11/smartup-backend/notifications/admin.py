from django.contrib import admin

from backend.admin import CreatedByModelAdmin

from .models import Notification

# Register your models here.


class NotificationAdmin(CreatedByModelAdmin):
    list_filter = ["is_read"]
    list_display = [
        "__str__",
        "user",
        "subject_type",
        "subject_id",
        "title",
        "is_read",
        "created_at",
        "id",
    ]
    search_fields = ["subject_id"]

    def body_summary(self, obj):
        if obj.body is not None:
            return obj.body[:100]
        return ""


admin.site.register(Notification, NotificationAdmin)
