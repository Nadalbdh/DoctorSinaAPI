# Generated by Django 3.2.3 on 2022-11-26 18:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0128_smsbroadcastrequest_number_of_days"),
    ]

    operations = [
        migrations.AddField(
            model_name="municipality",
            name="contract_signing_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
