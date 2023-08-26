from datetime import date

from django.contrib.auth.models import User
from django.db import transaction

from backend.default_municipality_objects import DEFAULT_COMMITTEES, DEFAULT_PROCEDURES
from backend.functions import get_manager_username_from_phone_number
from backend.helpers import (
    generate_default_password,
    get_lon_lat_attributes_from_coordinates,
    ManagerHelpers,
)
from backend.models import Committee, ComplaintCategory, Municipality, Procedure
from backend.services.notify_citizens import NotifyCitizensService
from backend.services.notify_new_managers import NotifyNewManagerService
from sms.sms_manager import SMSManager
from sms.tasks import flush_pending_sms


class MunicipalityOnBoardingService:
    def __init__(self, municipality: Municipality):
        self.municipality = municipality

    def activate(self):
        if self.municipality.is_active:
            return
        self.municipality.set_preferred_for_citizens()
        self.municipality.is_signed = True
        self.municipality.is_active = True
        self.municipality.activation_date = date.today()
        self.municipality.save()
        NotifyCitizensService(self.municipality).notify_all_active_citizens()
        flush_pending_sms.delay(self.municipality.pk)  # Send SMS that are in the queue

    def sign(self):
        if self.municipality.is_signed:
            return
        self.municipality.is_signed = True
        first_registred_manager = self.municipality.managers.filter(
            user__is_active=True
        ).order_by("user__date_joined")[0]
        if self.municipality.contract_signing_date is None and first_registred_manager:
            self.municipality.contract_signing_date = (
                first_registred_manager.user.date_joined.date()
            )
        self.municipality.save()

    def deactivate(self):
        if not self.municipality.is_active:
            return
        self.municipality.is_signed = False
        self.municipality.is_active = False
        self.municipality.activation_date = None
        self.municipality.save()

    # In case of an unexpected failure, rollback the on_boarding process
    @transaction.atomic
    def on_board(self, data):
        # Create the user for the manager
        user = User.objects.create(
            last_name=data["manager_fullname"],
            username=get_manager_username_from_phone_number(data["manager_number"]),
            email=data["manager_email"],
        )

        # Link the user to the municipality
        manager = self.municipality.managers.create(
            user=user, title=data["manager_title"]
        )
        cc = ComplaintCategory.objects.all()
        manager.complaint_categories.add(*cc)
        # Set the password and the permissions
        password = generate_default_password(user)
        ManagerHelpers(manager, self.municipality).assign_all_permissions()

        # Add the attributes for the municipality and activate it
        coordinates = get_lon_lat_attributes_from_coordinates(data["coordinates"])
        self.__add_defaults(
            longitude=coordinates[1],
            latitude=coordinates[0],
            name_fr=data["municipality_name_fr"],
            logo=data["logo"],
            website=data["website"],
            facebook_url=data["facebook_url"],
        )

        return password

    #######################################################################
    #                               Helpers                               #
    #######################################################################

    def __add_defaults(self, **kwargs):
        # Set municipality attributes
        for key, value in kwargs.items():
            setattr(self.municipality, key, value)

        # Add default items
        self.__add_committees()
        self.__add_procedures()

    def __add_committees(self):
        self.__bulk_create_related_objects(
            self.municipality.committees, Committee, DEFAULT_COMMITTEES
        )

    def __add_procedures(self):
        self.__bulk_create_related_objects(
            self.municipality.procedures, Procedure, DEFAULT_PROCEDURES
        )

    def __bulk_create_related_objects(self, queryset, model, objects):
        """
        Encapsulates the list comprehension and calling bulk_create.
        """
        return queryset.bulk_create(
            [model(municipality=self.municipality, **obj_dict) for obj_dict in objects]
        )
