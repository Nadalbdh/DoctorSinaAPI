from django.contrib import admin

from polls.models import Choice, Poll


class PollAdmin(admin.ModelAdmin):
    list_display = ["__str__", "starts_at", "ends_at", "municipality", "id"]
    search_fields = ["__str__"]
    list_filter = ["starts_at", "municipality"]


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["__str__", "poll", "votes_count"]


admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Poll, PollAdmin)
