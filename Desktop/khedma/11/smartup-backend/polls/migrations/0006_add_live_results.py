# Generated by Django 3.2.3 on 2021-11-11 20:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("polls", "0005_add_more_field_to_poll"),
    ]

    operations = [
        migrations.AddField(
            model_name="poll",
            name="live_results",
            field=models.BooleanField(default=False),
        ),
    ]
