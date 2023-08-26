# Generated by Django 2.2.7 on 2020-04-22 23:02
from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations


def add_gremda_as_default_municipality(apps, schema_editor):
    Citizen = apps.get_model("backend", "Citizen")
    Municipality = apps.get_model("backend", "Municipality")
    try:
        gremda = Municipality.objects.get(id=216)
        for citizen in Citizen.objects.all():
            if citizen.preferred_municipality is None:
                citizen.preferred_municipality = gremda
                citizen.save()
            if citizen.registration_municipality is None:
                citizen.registration_municipality = gremda
                citizen.save()
    except ObjectDoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0052_auto_20200422_2053"),
    ]

    operations = [
        migrations.RunPython(add_gremda_as_default_municipality),
    ]
