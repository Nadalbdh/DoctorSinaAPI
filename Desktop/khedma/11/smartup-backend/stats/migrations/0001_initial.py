# Generated by Django 3.2.3 on 2022-09-29 09:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("backend", "0120_dossier_created_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationUpdatePerformance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("average_first_response_days", models.IntegerField(default=0)),
                ("received_percentage", models.IntegerField(default=0)),
                ("processing_percentage", models.IntegerField(default=0)),
                ("accepted_percentage", models.IntegerField(default=0)),
                ("rejected_percentage", models.IntegerField(default=0)),
                ("not_clear_percentage", models.IntegerField(default=0)),
                ("invalid_percentage", models.IntegerField(default=0)),
                (
                    "municipality",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="performance",
                        to="backend.municipality",
                    ),
                ),
            ],
        ),
    ]
