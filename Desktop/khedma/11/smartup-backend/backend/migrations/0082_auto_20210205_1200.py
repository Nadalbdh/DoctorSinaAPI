# Generated by Django 2.2.17 on 2021-02-05 12:00
import json

from django.db import migrations


def add_mun_name_fr(apps, schema_editor):
    Municipality = apps.get_model("backend", "Municipality")
    with open("backend/fixtures/municipalities.json", encoding="utf-8") as muns_json:
        muns_dict = json.load(muns_json)
        for mun, mun_dict in zip(Municipality.objects.all().order_by("pk"), muns_dict):
            mun.name_fr = mun_dict["fields"]["name_fr"]
            mun.save()


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0081_municipality_name_fr"),
    ]

    operations = [migrations.RunPython(add_mun_name_fr)]
