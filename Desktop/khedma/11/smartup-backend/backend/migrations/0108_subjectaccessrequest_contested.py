# Generated by Django 3.2.3 on 2021-09-25 07:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0107_add_eticket_field_in_municipality"),
    ]

    operations = [
        migrations.AddField(
            model_name="subjectaccessrequest",
            name="contested",
            field=models.BooleanField(default=False),
        ),
    ]
