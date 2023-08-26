# Generated by Django 3.2.3 on 2021-10-06 16:34

from django.db import migrations
from guardian.shortcuts import get_users_with_perms


def get_managers_by_permission_per_municipality(municipality, permission):
    manager_users = get_users_with_perms(
        municipality, only_with_perms_in=[permission], attach_perms=True
    )
    return [user.manager for user in manager_users]


def update_manager_permissions_complaints(apps, schema_editor):
    Municipality = apps.get_model("backend", "Municipality")
    ComplaintCategory = apps.get_model("backend", "ComplaintCategory")
    categories = [c.pk for c in ComplaintCategory.objects.all()]
    for municipality in Municipality.objects.filter(is_active=True):
        managers = get_managers_by_permission_per_municipality(
            municipality, "MANAGE_COMPLAINTS"
        )
        for manager in managers:
            manager.complaint_categories.set(categories)
            manager.save()


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0110_merge_20211006_1623"),
    ]

    operations = [
        migrations.RunPython(update_manager_permissions_complaints),
    ]
