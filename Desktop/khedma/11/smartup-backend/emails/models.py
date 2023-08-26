from django.db import models

from backend.models import Municipality


class Email(models.Model):
    email = models.EmailField()
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, related_name="emails"
    )
