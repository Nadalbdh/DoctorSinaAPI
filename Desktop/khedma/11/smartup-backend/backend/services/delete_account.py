from datetime import datetime

from backend.exceptions import AccountCannotBeDeletedError
from backend.models import Citizen, Manager


def delete_account(user):
    current_timestamp = datetime.timestamp(datetime.now())
    name = (
        user.username + ";deleted;" + str(current_timestamp)
    )  # ; to split it if needed
    if not hasattr(user, "citizen") and not hasattr(user, "manager"):
        raise AccountCannotBeDeletedError
    user.username = name
    user.is_active = False
    user.save()
    if hasattr(user, "citizen"):
        citizen = Citizen.objects.get(user=user)
        citizen.is_deleted = True
        citizen.save()
    if hasattr(user, "manager"):
        manager = Manager.objects.get(user=user)
        manager.is_deleted = True
        manager.save()
