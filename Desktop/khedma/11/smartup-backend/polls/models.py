import rules
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Model, Q
from django.utils import timezone
from rules.contrib.models import RulesModelBase, RulesModelMixin

from backend.models import Municipality
from backend.rules import is_manager, is_manager_poll, rules
from polls.enum import PollStatus


class ChoiceType(models.TextChoices):
    SINGLE_CHOICE = "SINGLE_CHOICE", "اختيار واحد"
    MULTI_CHOICE = "MULTI_CHOICE", "اختيارات متعددة"


class Poll(RulesModelMixin, Model, metaclass=RulesModelBase):
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    text = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, related_name="polls"
    )
    picture = models.ImageField(null=True, blank=True, upload_to="polls/")
    kind = models.CharField(
        max_length=50, choices=ChoiceType.choices, default=ChoiceType.MULTI_CHOICE
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    live_results = models.BooleanField(default=False)

    def __str__(self):
        return self.text[:50]

    @property
    def remaining_time(self):
        """
        Return remaining time ( when poll started ) in minutes
        """
        now = timezone.now()
        if self.starts_at < now < self.ends_at:
            remaining = self.ends_at - now
            return remaining.total_seconds() // 60
        return None

    @property
    def starts_in(self):
        """
        Return remaining time ( when poll started ) in minutes
        """
        now = timezone.now()
        if self.starts_at > now:
            starts_in = self.starts_at - now
            return starts_in.total_seconds() // 60
        return None

    @property
    def status(self):
        now = timezone.now()
        if self.starts_at > now:
            return PollStatus.NOT_STARTED
        if self.ends_at < now:
            return PollStatus.ENDED
        return PollStatus.IN_PROGRESS

    class Meta:
        ordering = ["-created_at", "starts_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(ends_at__gt=F("starts_at")),
                name="check_date",
            ),
        ]
        rules_permissions = {
            "change": is_manager,
            "add": is_manager,
            "view": rules.always_allow,
            "delete": is_manager,
            "vote": rules.always_allow,
        }


class Choice(RulesModelMixin, Model, metaclass=RulesModelBase):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=250)
    voters = models.ManyToManyField(User, blank=True)
    picture = models.ImageField(null=True, blank=True, upload_to="polls/choices/")

    def __str__(self):
        return self.text[:50]

    @property
    def votes_count(self):
        return self.voters.count()

    class Meta:
        rules_permissions = {
            "change": is_manager_poll,
            "add": is_manager_poll,
            "view": rules.always_allow,
            "delete": is_manager_poll,
            "vote": rules.always_allow,
        }
