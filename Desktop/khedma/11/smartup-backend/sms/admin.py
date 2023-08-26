from django.contrib import admin

from sms.models import SMSQueueElement


class SMSQueueElementAdmin(admin.ModelAdmin):
    list_display = ["phone_number", "status", "municipality", "content", "os"]


admin.site.register(SMSQueueElement, SMSQueueElementAdmin)
