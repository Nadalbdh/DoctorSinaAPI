# Generated by Django 2.2.12 on 2020-10-19 14:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0065_auto_20200912_1140"),
    ]

    operations = [
        migrations.AddField(
            model_name="municipality",
            name="facebook_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]
