# Generated by Django 2.2.12 on 2020-09-12 11:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0064_municipality_website"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="committee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments",
                to="backend.Committee",
            ),
        ),
    ]
