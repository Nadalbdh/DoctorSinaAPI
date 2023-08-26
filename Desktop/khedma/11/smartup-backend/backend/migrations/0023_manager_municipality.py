# Generated by Django 2.2.7 on 2020-03-09 22:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0022_auto_20200304_2210"),
    ]

    operations = [
        migrations.AddField(
            model_name="manager",
            name="municipality",
            field=models.ForeignKey(
                default=216,
                on_delete=django.db.models.deletion.CASCADE,
                to="backend.Municipality",
            ),
            preserve_default=False,
        ),
    ]
