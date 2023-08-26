# Generated by Django 2.2.7 on 2020-04-19 16:12

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0047_auto_20200419_1605"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="municipality",
            options={
                "ordering": ["-is_active"],
                "permissions": (
                    ("MANAGE_DOSSIERS", "Gerer les dossiers et demandes"),
                    ("MANAGE_PROCEDURES", "Gérer les procedures de la commune"),
                    ("MANAGE_COMPLAINTS", "Gérer les plaintes des citoyens"),
                    ("MANAGE_REPORTS", "Gerer les rapports du conseil municipal"),
                    (
                        "MANAGE_SUBJECT_ACCESS_REQUESTS",
                        "Gerer les demandes d'acces à l'information",
                    ),
                    ("MANAGE_COMMITTEES", "Gerer les comités du conseil municipal"),
                    ("MANAGE_NEWS", "Gerer les actualités de la commune"),
                    ("MANAGE_EVENTS", "Gerer les événements"),
                    (
                        "MANAGE_PERMISSIONS",
                        "Gerer les permissions de chaque membre sur la plateforme",
                    ),
                ),
                "verbose_name_plural": "Municipalities",
            },
        ),
    ]
