# Generated by Django 2.2.7 on 2020-03-15 01:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0025_subjectaccessrequest_is_public"),
    ]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="is_public",
            field=models.BooleanField(default=True),
        ),
    ]
