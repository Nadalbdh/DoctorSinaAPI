import random
from typing import Iterable

from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm, get_users_with_perms

from backend.enum import MunicipalityPermissions
from backend.models import Manager, Municipality
from settings.settings import FRONTEND_URL


class ManagerHelpers:
    # TODO move all code that is relevant for managers into this file
    permission_list = [
        key for (key, value) in list(MunicipalityPermissions.get_choices())
    ]

    def __init__(self, manager: Manager, municipality: Municipality):
        if not manager.user:
            raise TypeError("Manager must be linked to a user")
        self.manager, self.municipality = manager, municipality

    def assign_all_permissions(self):
        """
        Assign all permissions to the given user for the given municipality
        """
        self.assign_permissions(self.permission_list)

    def assign_permissions(self, permissions):
        """
        Assign a list of  permissions to the given user for the given municipality
        """
        for permission in permissions:
            assign_perm(permission, self.manager.user, self.municipality)


def get_managers_by_permission_per_municipality(
    municipality, permission
) -> Iterable[Manager]:
    manager_users = get_users_with_perms(
        municipality, only_with_perms_in=[permission], attach_perms=True
    )
    formatted_result = [user.manager for user in manager_users]
    return formatted_result


def get_frontend_url(municipality: Municipality):
    return f"{FRONTEND_URL}/{municipality.get_route_name()}"


def get_lon_lat_attributes_from_coordinates(coordinates):
    coordinates.replace(" ", "")
    return str.split(coordinates, ",")


def generate_default_password(user: User) -> str:
    """
    sets a new password of length 5
    returns the password
    """
    tmp = random.randint(0, 99999)
    password = f"{tmp}".zfill(5)
    user.set_password(password)  # This doesn't save the instance
    user.save()
    return password


def get_unique_identifier(model):
    """
    unique_identifier is different from  the id (primary key)
    """
    unique_identifier_random = random.randint(100, 1000000000)
    while model.objects.filter(unique_identifier=unique_identifier_random).exists():
        unique_identifier_random = random.randint(100, 1000000000)
    return unique_identifier_random
