# Generated by Django 2.2.7 on 2020-01-27 01:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0004_auto_20200126_2316"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complaint",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="complaints/"),
        ),
    ]
