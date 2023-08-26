from django.contrib.auth.models import User

from backend.helpers import get_managers_by_permission_per_municipality
from backend.models import Municipality

from .models import Notification


def notify_managers_for(permission: str, municipality: Municipality, **kwargs) -> None:
    """
    notify all manager that using the updatable_instance notification template
    """
    managers = get_managers_by_permission_per_municipality(municipality, permission)
    notifications = [
        Notification(user=manager.user, municipality=municipality, **kwargs)
        for manager in managers
    ]
    Notification.objects.bulk_create(notifications)
