from django.contrib.auth.models import User
from django.db import models


class APILog(models.Model):
    api_url = models.CharField(max_length=1024, help_text="API URL")
    body = models.TextField()
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        help_text="The user who made the request",
        blank=True,
        null=True,
    )
    method = models.CharField(max_length=10, db_index=True)
    client_ip = models.CharField(max_length=50)
    status_code = models.PositiveSmallIntegerField(
        help_text="Response status code", db_index=True
    )
    execution_time = models.DecimalField(
        decimal_places=5,
        max_digits=8,
        help_text="Server execution time (Not complete response time.)",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.api_url

    class Meta:
        verbose_name = "API Log"
        verbose_name_plural = "API Logs"
        ordering = ("-timestamp",)
