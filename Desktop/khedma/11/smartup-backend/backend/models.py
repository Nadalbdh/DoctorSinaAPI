from datetime import date, timedelta

import rules
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import (
    CASCADE,
    Case,
    Count,
    Model,
    OuterRef,
    Q,
    SET_NULL,
    Subquery,
    Value,
    When,
)
from django.utils import timezone
from django.utils.text import slugify
from rules.contrib.models import RulesModelBase, RulesModelMixin

import backend.rules as brules
from backend.decorators import prefix_citizen_url
from backend.enum import (
    DossierTypes,
    ForumTypes,
    GenderType,
    MunicipalityPermissions,
    NewsCategory,
    OsTypes,
    ProcedureTypes,
    ReactionsTypes,
    RequestStatus,
    SMSBroadcastRequestStatus,
    SMSBroadcastRequestTarget,
    StatusLabel,
    TopicStates,
    TunisianCities,
)
from backend.functions import (
    get_file_url,
    get_image_url,
    get_manager_phone_number_from_username,
    is_citizen,
    is_manager,
)
from backend.notification_helpers import excerpt_notification
from emails.templatetags.status_translation import status_translate
from notifications.models import NotifiableModel, Notification

# Manager of Django class 'Municipality'


class MunicipalityManager(models.Manager):
    def active(self):
        return self.get_queryset().filter(is_active=True)


class Status(models.TextChoices):
    DEACTIVATED = "DEACTIVATED", "غير مفعل"
    IN_PROGRESS = "IN_PROGRESS", "التفعيل جري"
    ACTIVATED = "ACTIVATED", "مفعل"


class StatusCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 20
        kwargs["choices"] = Status.choices
        if "default" not in kwargs:
            kwargs["default"] = Status.ACTIVATED
        super().__init__(*args, **kwargs)


class Municipality(Model):
    # Model Manager:
    objects = MunicipalityManager()

    # Model attributes
    name = models.CharField(max_length=255)
    name_fr = models.CharField(max_length=255)
    city = models.CharField(choices=TunisianCities.get_choices(), max_length=255)
    is_active = models.BooleanField(default=False)
    is_signed = models.BooleanField(default=False)
    logo = models.ImageField(null=True, blank=True, upload_to="municipalities_logos/")
    latitude = models.DecimalField(max_digits=10, default=36.797423, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, default=10.165894, decimal_places=7)
    website = models.URLField(null=True, blank=True)
    facebook_url = models.URLField(max_length=300, null=True, blank=True)
    sms_credit = models.IntegerField(default=500)
    population = models.IntegerField(default=0)
    total_sms_consumption = models.IntegerField(default=0)
    has_eticket = models.BooleanField(default=False)
    activation_date = models.DateField(null=True, blank=True)
    contract_signing_date = models.DateField(null=True, blank=True)

    # Feature status of the municipality

    service_eticket = StatusCharField(default=Status.DEACTIVATED)
    service_dossiers = StatusCharField()
    service_complaints = StatusCharField()
    service_sar = StatusCharField()
    service_procedures = StatusCharField()
    service_news = StatusCharField()
    service_forum = StatusCharField()
    service_reports = StatusCharField()
    service_events = StatusCharField()

    broadcast_frequency = models.DurationField(default=timezone.timedelta(weeks=1))
    last_broadcast = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Municipalities"
        permissions = MunicipalityPermissions.get_choices()
        ordering = ["-is_active", "-is_signed"]  # make active municipalities show first

    def __str__(self):
        return "{:20.20}: {}".format(self.city, self.name)

    # TODO refactor this into a service ex:
    #  MunicipalityStatsService(municipality).calculate_total_registered()
    #  MunicipalityStatsService(municipality).calculate_total_starred()..
    def total_registered(self):
        return self.registered_citizens.all().count()

    def total_starred(self):
        return self.starred_citizens.all().count()

    def total_followed(self):
        return self.citizens.all().count()

    def managers_count(self):
        return self.managers.filter(is_deleted=False).count()

    def last_sms_broadcast(self):
        return (
            self.sms_broadcast_requests.filter(status="SENT")
            .order_by("-scheduled_on")
            .first()
        )

    def can_broadcast(self):
        if self.last_broadcast is None:
            return True
        return self.last_broadcast + self.broadcast_frequency <= timezone.now()

    def set_last_broadcast(self, datetime=None):
        if not datetime:
            datetime = timezone.now()
        self.last_broadcast = datetime
        self.save()

    def get_route_name(self):
        return slugify(self.name_fr)

    def to_dict(self):
        from etickets.serializers import AgencySerializer

        return {
            "id": self.id,
            "name": self.name,
            "name_fr": self.name_fr,
            "city": self.city,
            "logo": get_image_url(self.logo),
            "is_active": self.is_active,
            "is_signed": self.is_signed,
            "partner_associations": [
                association.to_dict()
                for association in self.partner_associations.all().order_by("id")
            ],
            "regions": [region.to_dict() for region in self.regions.all()],
            "longitude": self.longitude,
            "latitude": self.latitude,
            "website": self.website,
            "facebook_url": self.facebook_url,
            "total_followers": self.total_followed(),
            "has_eticket": self.has_eticket,
            "agency": AgencySerializer(self.agencies.all(), many=True).data,
            "service_eticket": self.service_eticket,
            "service_dossiers": self.service_dossiers,
            "service_complaints": self.service_complaints,
            "service_sar": self.service_sar,
            "service_procedures": self.service_procedures,
            "service_news": self.service_news,
            "service_forum": self.service_forum,
            "service_reports": self.service_reports,
            "service_events": self.service_events,
            "route_name": self.get_route_name(),
            "sms_credit": self.sms_credit,
            "total_sms_consumption": self.total_sms_consumption,
            "population": self.population,
            "broadcast_frequency": self.broadcast_frequency,
            "last_broadcast": self.last_broadcast,
            "activation_date": self.activation_date,
            "contract_signing_date": self.contract_signing_date,
        }

    def to_simplified_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_fr": self.name_fr,
            "city": self.city,
            "is_active": self.is_active,
            "is_signed": self.is_signed,
            "has_eticket": self.has_eticket,
            "logo": get_image_url(self.logo),
            "longitude": self.longitude,
            "latitude": self.latitude,
            "route_name": self.get_route_name(),
            "activation_date": self.activation_date,
        }

    def set_preferred_for_citizens(self):
        citizens = Citizen.objects.all().filter(registration_municipality=self)
        # TODO Notify users (logic for users should be done in a service)
        for citizen in citizens:
            citizen.preferred_municipality = self
            citizen.save()
            citizen.municipalities.add(self)

    def summary_email_list(self):
        return self.emails.values_list("email", flat=True)


class CommitteeManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            # Integrating ordering according to counts in the META class didn't work
            .annotate(count_reports=Count("reports"))
            .annotate(
                major_order=Case(
                    When(title="المجلس البلدي", then=Value(0)),
                    default=Value(1),
                    output_field=models.IntegerField(),
                )
            )
            .order_by("major_order", "-count_reports")
        )


class Committee(Model):
    objects = CommitteeManager()
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="committees"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return "Municipality:{} committee: {}".format(
            self.municipality.name, self.title
        )

    def to_dict(self):
        return {
            "municipality_id": self.municipality_id,
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "number_of_reports": self.reports.count(),
        }


class Citizen(Model):
    # Assumption: user.username contains the user phone number
    user = models.OneToOneField(User, on_delete=CASCADE)
    cin_number = models.CharField(max_length=8, null=True, blank=True)
    function = models.CharField(max_length=255, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    facebook_account = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(max_length=255, null=True, blank=True)
    profile_picture = models.ImageField(
        null=True, blank=True, upload_to="profile_pictures"
    )
    validation_code = models.CharField(max_length=6, null=True, blank=True)
    # All municipalities followed by the user
    municipalities = models.ManyToManyField(Municipality, related_name="citizens")
    # Last chosen municipality
    preferred_municipality = models.ForeignKey(
        Municipality, related_name="starred_citizens", on_delete=CASCADE
    )
    # Municipality chosen on registration
    registration_municipality = models.ForeignKey(
        Municipality, related_name="registered_citizens", on_delete=CASCADE
    )
    first_login = models.BooleanField(default=True)
    gender = models.CharField(
        choices=GenderType.get_choices(), max_length=40, null=True, blank=True
    )
    see_ambassadors_forms = models.BooleanField(default=False)
    see_broadcast_forms = models.BooleanField(default=False)
    latest_residence_update_date = models.DateField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name()

    def get_username(self):
        return self.user.username

    def get_full_name(self):
        return self.user.get_full_name()

    def is_active(self):
        return self.user.is_active

    def last_login(self):
        return self.user.last_login

    def date_joined(self):
        return self.user.date_joined

    def set_first_login(self):
        self.first_login = False
        self.save()

    def to_dict(self):
        return {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "cin_number": self.cin_number,
            "function": self.function,
            "birth_date": self.birth_date,
            "email": self.user.email,
            "phone_number": self.user.username,
            "address": self.address,
            "facebook_account": self.facebook_account,
            "municipalities": list(self.municipalities.values_list("id", flat=True)),
            "preferred_municipality_id": self.preferred_municipality_id,
            "registration_municipality_id": self.registration_municipality_id,
            "fist_login": self.first_login,  # TODO: notify frontend teams, will be removed in Feb 2021
            "first_login": self.first_login,
            "profile_picture": get_image_url(self.profile_picture),
            "gender": self.gender,
            "latest_residence_update_date": self.latest_residence_update_date,
            "is_deleted": self.is_deleted,
        }


class Manager(Model):
    # Assumption: user.username contains the user phone number
    user = models.OneToOneField(User, on_delete=CASCADE)
    municipality = models.ForeignKey(
        "Municipality", on_delete=CASCADE, related_name="managers"
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    complaint_categories = models.ManyToManyField(
        "ComplaintCategory", related_name="managers"
    )
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return "Manager {} {}".format(self.user.get_full_name(), self.municipality)

    def get_phone_number(self):
        return get_manager_phone_number_from_username(self.user.username)

    def is_active(self):
        return self.user.is_active

    def last_login(self):
        return self.user.last_login

    def date_joined(self):
        return self.user.date_joined

    def to_dict(self):
        return {
            "id": self.user.id,
            "manager_id": self.id,
            "phone_number": self.get_phone_number(),
            "name": self.user.get_full_name(),
            "email": self.user.email,
            "title": self.title,
            "is_active": self.user.is_active,
            "is_deleted": self.is_deleted,
            "complaint_categories": [
                category.name for category in self.complaint_categories.all()
            ],
        }


class RegisteredDevice(Model):
    user = models.ForeignKey(User, related_name="devices", on_delete=CASCADE)
    device_unique_id = models.CharField(max_length=50, null=True, blank=True)
    os = models.CharField(max_length=40, null=True, choices=OsTypes.get_choices())  # OS
    os_version = models.CharField(max_length=40, null=True)  # OS Version
    fcm_token = models.CharField(max_length=200, null=True, blank=True)
    last_login = models.DateTimeField(auto_now=True, null=True, blank=True)
    last_version = models.CharField(max_length=10, null=True, blank=True)
    model = models.CharField(max_length=70, null=True)
    product = models.CharField(max_length=70, null=True)

    def __str__(self):
        return "Device: {}".format(self.owner_name())

    def owner_name(self):
        return self.user.get_full_name()


class OperationUpdate(models.Model):
    """Usage: operation_update.subject_access_request.citizen or subject_access_request.operation_update.status"""

    status = models.CharField(
        max_length=255,
        choices=RequestStatus.get_choices(),
        default=RequestStatus.RECEIVED,
    )
    note = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    operation = GenericForeignKey("content_type", "object_id")  # key we'll use
    image = models.ImageField(
        null=True, blank=True, default=None, upload_to="operation-updates"
    )
    # Foreign key management using ContentType
    limit = (
        models.Q(app_label="backend", model="complaint")
        | models.Q(app_label="backend", model="dossier")
        | models.Q(app_label="backend", model="subjectaccessrequest")
        | models.Q(app_label="backend", model="comment")
        | models.Q(app_label="backend", model="reservation")
    )
    content_type = models.ForeignKey(
        ContentType, limit_choices_to=limit, on_delete=CASCADE
    )
    object_id = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, null=True, on_delete=SET_NULL)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "{}: {}".format(self.operation, self.status)

    @property
    def created_by_name(self):
        return self.created_by.get_full_name() if self.created_by is not None else None

    @staticmethod
    def get_updates(obj):
        return [
            {
                "id": operation_update.id,
                "date": operation_update.created_at,
                "status": operation_update.status,
                "note": operation_update.note,
                # Why doesn't python have applicatives? T_T
                "created_by": operation_update.created_by.id
                if operation_update.created_by is not None
                else None,
                "created_by_name": operation_update.created_by_name,
                "image": operation_update.image.url
                if operation_update.image and hasattr(operation_update.image, "url")
                else "",
            }
            for operation_update in obj.operation_updates.all()
        ]


class LastUpdateManager(models.Manager):
    def get_queryset(self):
        """
        Annotate the objects with the status of the last operation update
        and its date.
        """
        queryset = super().get_queryset()
        # TODO check if we can cache this
        content_type = ContentType.objects.get_for_model(self.model)
        nested_base_query = OperationUpdate.objects.filter(
            content_type=content_type, object_id=OuterRef("pk")
        )[:1]
        # Trust the query optimizer
        return queryset.annotate(
            last_update=Subquery(nested_base_query.values("created_at")),
            last_status=Subquery(nested_base_query.values("status")),
        ).order_by("-last_update")


class UpdatableModel(Model):
    """
    Updatable models are models that have operation updates. The abstract
    model provides a custom save method to create the first status, and
    a custom manager that provides the date and status of the last operation-
    update.
    """

    # The extra fields last_update (time of the last update) and
    # last_status (status of the last update) are provided.
    objects = LastUpdateManager()

    class Meta:
        abstract = True

    @property
    def last_operation_update(self):
        """
        Returns the last operation update
        """
        return self.operation_updates.first()  # pylint: disable=no-member

    @property
    def status(self):
        """status of latest update"""
        last_update = self.last_operation_update
        return last_update.status if last_update is not None else None

    def save(self, *args, **kwargs):
        if not self.pk:
            created_by = getattr(self, "created_by", None)
            super().save(*args, **kwargs)
            OperationUpdate.objects.create(
                note="",
                status=RequestStatus.RECEIVED,
                operation=self,
                created_by=created_by,
            )
        else:
            super().save(*args, **kwargs)


class CountableModel(Model):
    hits = GenericRelation("Hit", related_query_name="%(class)s")

    class Meta:
        abstract = True

    @property
    def hits_count(self):
        """
        Returns hit count for an object
        """
        return self.hits.count()

    def hits_in_last(self, **kwargs):
        """
        Returns hit count for an object during a given time period.
        For example: hits_in_last(days=7).
        Accepts days, seconds, microseconds, milliseconds, minutes,
        hours, and weeks.  It's creating a timzeone.timedelta object.
        """
        assert kwargs, "Must provide at least one timedelta arg (eg, days=1)"

        period = timezone.now() - timezone.timedelta(**kwargs)
        return self.hits.filter(created_at__gte=period).count()


class SubjectAccessRequest(CountableModel, UpdatableModel, NotifiableModel):
    # User who created the request
    created_by = models.ForeignKey(User, on_delete=CASCADE)
    municipality = models.ForeignKey(
        "Municipality", on_delete=CASCADE, related_name="subject_access_requests"
    )
    document = models.CharField(max_length=200)
    is_public = models.BooleanField(default=True)
    structure = models.CharField(max_length=200)
    reference = models.CharField(max_length=200, blank=True, null=True)
    # Requested Access
    on_spot_document = models.BooleanField(default=False)
    printed_document = models.BooleanField(default=False)
    electronic_document = models.BooleanField(default=False)
    parts_of_document = models.BooleanField(default=False)
    contested = models.BooleanField(default=False)

    note = models.CharField(max_length=1000, null=True, blank=True)
    attachment = models.FileField(
        null=True, blank=True, upload_to="subject-access-requests/files/"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    operation_updates = GenericRelation(
        "OperationUpdate", related_query_name="subject_access_request"
    )
    notifications = GenericRelation(
        Notification,
        related_query_name="subject_access_request",
        content_type_field="subject_type",
        object_id_field="subject_id",
    )
    followers = models.ManyToManyField(
        User, related_name="subject_access_requests", blank=True
    )
    notification_title = "رد على  مطلب نفاذ إلى المعلومة خاص بي"

    @property
    @prefix_citizen_url
    def citizen_url(self):
        return f"accesinfo/{self.id}"

    @property
    def contact_number(self):
        return self.created_by.username

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "{}: {}".format(self.created_at, self.document)

    def get_notification_body(self):
        template = 'تم الرد على مطلب النفاذ إلى المعلومة : "{}" ب "{}"'
        return template.format(
            excerpt_notification(self.document), status_translate(self.status)
        )

    def get_notifiable_users(self):
        return [self.created_by]


class Region(Model):
    name = models.CharField(max_length=50)
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="regions"
    )

    def __str__(self):
        return "{} {}".format(self.municipality, self.name)

    def to_dict(self):
        return {
            "id": self.pk,
            "name": self.name,
            "municipality_id": self.municipality_id,
        }


class ComplaintCategoryManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                major_order=Case(
                    When(name="أخرى", then=Value(1)),
                    default=Value(0),
                    output_field=models.IntegerField(),
                )
            )
            .order_by("major_order", "name")
        )


class ComplaintCategory(Model):
    name = models.CharField(max_length=50)
    objects = ComplaintCategoryManager()

    class Meta:
        verbose_name_plural = "complaint categories"

    def __str__(self):
        return self.name or f"Category {self.id}"

    def to_dict(self):
        return {
            "id": self.pk,
            "name": self.name,
            "sub_categories": [
                sub_category.to_dict(show_category=False)
                for sub_category in self.sub_categories.all()
            ],
        }


class ComplaintSubCategory(Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(
        ComplaintCategory, on_delete=CASCADE, related_name="sub_categories"
    )

    class Meta:
        unique_together = ["name", "category"]
        verbose_name_plural = "complaint subcategories"

    def __str__(self):
        return "{} {}".format(self.category, self.name)

    def to_dict(self, show_category=True):
        data = {
            "id": self.pk,
            "name": self.name,
        }
        if show_category:
            data["category_name"] = self.category.name
        return data


class Complaint(
    RulesModelMixin,
    UpdatableModel,
    CountableModel,
    NotifiableModel,
    metaclass=RulesModelBase,
):
    created_by = models.ForeignKey(User, on_delete=CASCADE)
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="complaints"
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=7, null=True, blank=True
    )
    address = models.TextField(null=True, blank=True)
    problem = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    image = models.ImageField(null=True, blank=True, upload_to="complaints/")
    created_at = models.DateTimeField(auto_now_add=True)
    operation_updates = GenericRelation(
        "OperationUpdate", related_query_name="complaint"
    )
    reactions = GenericRelation("Reaction", related_query_name="complaint")
    notifications = GenericRelation(
        Notification,
        related_query_name="complaint",
        content_type_field="subject_type",
        object_id_field="subject_id",
    )
    region = models.ForeignKey(Region, on_delete=SET_NULL, null=True, blank=True)
    category = models.ForeignKey(ComplaintCategory, on_delete=SET_NULL, null=True)
    sub_category = models.ForeignKey(
        ComplaintSubCategory, on_delete=SET_NULL, null=True
    )
    followers = models.ManyToManyField(User, related_name="complaints", blank=True)
    notification_title = "تحيين في مشكل خاص بي"

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="consistent_address",
                check=(Q(address__isnull=False) | ~Q(address__exact=""))
                | (Q(longitude__isnull=False) & Q(latitude__isnull=False)),
            )
        ]
        ordering = ["-created_at"]

        rules_permissions = {
            "opupdate": brules.has_category_permission,
            "change": brules.has_category_permission | brules.is_owner,
            "add": rules.always_allow,
            "view": rules.always_allow,
            "delete": brules.is_owner,
        }

    def __str__(self):
        return "Complaint {}: {}".format(self.created_at, self.problem[:30])

    @property
    def contact_number(self):
        return self.created_by.username

    @property
    @prefix_citizen_url
    def citizen_url(self):
        return f"plaintes/{self.id}"

    @property
    def score(self):
        # TODO test me
        return sum(self.reactions.values_list("value", flat=True))

    @property
    def created_by_username(self):
        # TODO test me
        return self.created_by.get_full_name()

    def user_vote(self, user):
        # TODO test me
        return sum(self.reactions.filter(user=user).values_list("value", flat=True))

    def to_dict(self, user=None):
        data = {
            "id": self.id,
            "municipality_id": self.municipality_id,
            "problem": self.problem,
            "image": get_image_url(self.image),
            "solution": self.solution,
            "is_public": self.is_public,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "address": self.address,
            "created_by": self.created_by.get_full_name(),
            "created_by_id": self.created_by.id,
            "created_at": self.created_at,
            "updates": OperationUpdate.get_updates(self),
            "score": self.score,
            "followers": list(self.followers.all().values_list("id", flat=True)),
            "category": self.category.name if self.category else None,
            "sub_category": self.sub_category.name if self.sub_category else None,
            "region": self.region.name if self.region_id else None,
            "hits": self.hits_count,
            "contact_number": self.contact_number,
        }
        if user and user.is_authenticated:
            data["user_vote"] = self.user_vote(user)
        return data

    def get_notification_body(self):
        template = 'تم تحيين وضعية المشكل "{}" إلى "{}".'
        return template.format(
            excerpt_notification(self.problem), status_translate(self.status)
        )

    def get_notifiable_users(self):
        return [self.created_by]


class Dossier(
    RulesModelMixin, UpdatableModel, NotifiableModel, metaclass=RulesModelBase
):
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="dossiers"
    )
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=50, choices=DossierTypes.get_choices(), default=DossierTypes.OTHER
    )
    unique_identifier = models.CharField(max_length=20)
    cin_number = models.TextField(max_length=8)
    deposit_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=SET_NULL, null=True)
    followers = models.ManyToManyField(User, related_name="dossiers")
    operation_updates = GenericRelation("OperationUpdate", related_query_name="dossier")
    notifications = GenericRelation(
        Notification,
        related_query_name="dossier",
        content_type_field="subject_type",
        object_id_field="subject_id",
    )

    phone_number = models.CharField(max_length=8, null=True, blank=True)
    notification_title = "تحيين في مطلب رخصة "

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["unique_identifier", "municipality"],
                name="unique_per_municipality",
            )
        ]

        rules_permissions = {
            "opupdate": brules.has_dossier_permission,
            "change": brules.has_dossier_permission | brules.is_owner,
            "add": rules.always_allow,
            "view": brules.has_dossier_permission
            | brules.is_owner
            | brules.is_follower,
            "delete": brules.is_owner | brules.has_dossier_permission,
        }

    @property
    def created_by_username(self):
        return self.created_by.get_full_name()

    @property
    def contact_number(self):
        subscribers = [
            phone_number
            for phone_number in self.followers.all().values_list("username", flat=True)
        ]
        if self.phone_number and self.phone_number not in subscribers:
            subscribers.append(self.phone_number)
        return subscribers

    @property
    @prefix_citizen_url
    def citizen_url(self):
        return "dossiers"

    def __str__(self):
        return "{}: {}".format(self.created_at, self.unique_identifier)

    def to_dict(self):
        return {
            "municipality_id": self.municipality_id,
            "id": self.id,
            "name": self.name,
            "unique_identifier": self.unique_identifier,
            "cin_number": self.cin_number,
            "deposit_date": self.deposit_date,
            "followers_ids": list(self.followers.all().values_list("id", flat=True)),
            "created_at": self.created_at,
            "type": self.type,
            "updates": OperationUpdate.get_updates(self),
            "phone_number": self.phone_number,
        }

    def get_notification_body(self):
        template = 'تم  تحيين وضعية المطلب البلدي عدد {} إلى  "{}".'
        return template.format(
            excerpt_notification(self.unique_identifier), status_translate(self.status)
        )

    def get_notifiable_users(self):
        return self.followers.all()


class Building(RulesModelMixin, Model, metaclass=RulesModelBase):
    dossier = models.OneToOneField(Dossier, on_delete=CASCADE)
    address = models.CharField(max_length=50)
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=7, null=True, blank=True
    )
    permit_reference = models.CharField(max_length=50)
    image = models.ImageField(null=True, blank=True, upload_to="buildings/")

    class Meta:
        rules_permissions = {
            "change": brules.is_owner_of_related_dossier,
            "add": rules.always_allow,
            "view": brules.is_owner_of_related_dossier
            | brules.is_follower_of_related_dossier
            | brules.has_dossier_permission,
            "delete": brules.is_owner_of_related_dossier,
        }


class DossierAttachment(RulesModelMixin, Model, metaclass=RulesModelBase):
    dossier = models.ForeignKey(Dossier, on_delete=CASCADE, related_name="attachments")
    attachment = models.FileField(null=True, blank=True, upload_to="dossiers/files/")
    image = models.ImageField(null=True, blank=True, upload_to="dossiers/images/")
    name = models.CharField(max_length=100)
    file_name = models.CharField(max_length=100)

    class Meta:
        rules_permissions = {
            "change": brules.is_owner_of_related_dossier,
            "add": rules.always_allow,
            "view": brules.is_owner_of_related_dossier
            | brules.is_follower_of_related_dossier
            | brules.has_dossier_permission,
            "delete": brules.is_owner_of_related_dossier,
        }


class Topic(Model):
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="topics"
    )
    label = models.CharField(max_length=200)
    state = models.CharField(
        max_length=50, choices=TopicStates.get_choices(), default=TopicStates.HIDDEN
    )
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["municipality", "label"]
        ordering = ["-created_at"]

    def __str__(self):
        return "{} {}".format(self.municipality, self.label)

    def to_dict(self):
        # FIXME remove this when it's no longer needed
        return {
            "municipality_id": self.municipality.pk,
            "id": self.id,
            "label": self.label,
            "state": self.state,
            "description": self.description,
            "created_at": self.created_at,
        }


class PostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(parent_comment=None)

    use_in_migrations = True


class CommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(parent_comment=None)

    use_in_migrations = True


class Comment(UpdatableModel, CountableModel, NotifiableModel):
    """
    Assumption:
        Posts are also comments having:
            parent_comment == None
            and
            municipality != None
    """

    created_by = models.ForeignKey(User, on_delete=CASCADE)
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="all_comments"
    )
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    committee = models.ForeignKey(
        Committee,
        null=True,
        blank=True,
        on_delete=SET_NULL,
        related_name="all_comments",
    )
    image = models.ImageField(null=True, blank=True, upload_to="comments/")
    parent_comment = models.ForeignKey(
        "self", on_delete=CASCADE, null=True, blank=True, related_name="sub_comments"
    )
    reactions = GenericRelation("Reaction", related_query_name="comment")
    notifications = GenericRelation(
        Notification,
        related_query_name="comment",
        content_type_field="subject_type",
        object_id_field="subject_id",
    )
    type = models.CharField(
        max_length=50,
        choices=ForumTypes.get_choices(),
        default=ForumTypes.SUGGESTION,
        null=True,
        blank=True,
    )
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=SET_NULL)
    operation_updates = GenericRelation("OperationUpdate", related_query_name="comment")
    followers = models.ManyToManyField(User, related_name="comments", blank=True)
    notification_title = "تحيين في المقترح خاص بي"

    objects = LastUpdateManager()
    posts = PostManager()
    comments = CommentManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "{} {}: {}".format(self.id, self.created_at, self.title)

    def get_topic(self):
        if self.topic:
            return self.topic.to_dict()
        return ""

    @property
    def contact_number(self):
        return self.created_by.username

    @property
    @prefix_citizen_url
    def citizen_url(self):
        return f"forum/{self.id}"

    def to_dict(self, include_sub_comments=True, user=None):
        data = {
            "id": self.id,
            "municipality_id": self.municipality_id,
            "title": self.title,
            "body": self.body,
            "excerpt": self.body[:80] + " ... " if self.body else self.title,
            "created_at": self.created_at,
            "committee_id": self.committee_id,
            "committee_title": self.committee.title if self.committee else "",
            "image": get_image_url(self.image),
            "created_by_id": self.created_by_id,
            "user_fullname": self.created_by.get_full_name(),
            "followers": list(self.followers.all().values_list("id", flat=True)),
            "is_manager": is_manager(self.created_by),
            "topic": self.get_topic(),
            "type": self.type,
            "score": sum(self.reactions.values_list("value", flat=True)),
            "parent_comment_id": self.parent_comment_id,
            "updates": OperationUpdate.get_updates(self),
            "hits": self.hits_count,
        }
        if include_sub_comments:
            data["sub_comments"] = [
                sub_comment.to_dict() for sub_comment in self.sub_comments.all()
            ]
        if user and user.is_authenticated:
            data["user_vote"] = sum(
                self.reactions.filter(user=user).values_list("value", flat=True)
            )
        return data

    def get_notification_body(self):
        template = 'تم تحيين وضعية المقترح "{}" إلى "{}".'
        choices = dict(
            StatusLabel.get_choices().get("FRONTOFFICE_LABEL")
        )  # TODO refactor this
        latest_update = choices.get(self.type)
        return template.format(
            excerpt_notification(self.body), latest_update.get(self.status)
        )

    def get_notifiable_users(self):
        return [self.created_by]


class Reaction(Model):
    user = models.ForeignKey(User, on_delete=CASCADE)
    type = models.CharField(max_length=10, choices=ReactionsTypes.get_choices())
    value = models.IntegerField()
    post = GenericForeignKey("content_type", "object_id")  # key we'll use

    # Foreign key management using ContentType
    limit = (
        models.Q(app_label="backend", model="comment")
        | models.Q(app_label="backend", model="complaint")
        | models.Q(app_label="backend", model="news")
    )
    content_type = models.ForeignKey(
        ContentType, limit_choices_to=limit, on_delete=CASCADE
    )
    object_id = models.PositiveIntegerField()


class Hit(Model):
    """
    Model Captures a single hit/view by a visitor
    """

    created_at = models.DateTimeField(editable=False, auto_now_add=True, db_index=True)
    citizen = models.ForeignKey(
        Citizen, null=True, editable=False, on_delete=models.CASCADE
    )

    object = GenericForeignKey("content_type", "object_id")
    content_type = models.ForeignKey(ContentType, on_delete=CASCADE)
    object_id = models.PositiveIntegerField()

    class Meta:
        ordering = ("-created_at",)
        get_latest_by = "created_at"
        verbose_name = "hit"
        verbose_name_plural = "hits"


class News(CountableModel):
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="news"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
    committee = models.ForeignKey(Committee, on_delete=SET_NULL, null=True, blank=True)
    attachment = models.FileField(null=True, blank=True, upload_to="news/files/")
    reactions = GenericRelation("Reaction", related_query_name="news")
    to_broadcast = models.BooleanField(default=False)
    category = models.CharField(
        max_length=50,
        choices=NewsCategory.get_choices(),
        default=NewsCategory.ANNOUNCEMENT,
    )
    tags = models.ManyToManyField("NewsTag", related_name="news", blank=True)

    class Meta:
        verbose_name_plural = "news"
        verbose_name = "news_object"
        ordering = ["-published_at"]

    def __str__(self):
        return "{}: {}".format(self.committee, self.title)

    def excerpt(self):
        return self.body[:80] + " .. "

    def to_dict(self, user=None):
        first_image = None
        if self.images.count() != 0:
            first_image = self.images.all()[0]
        data = {
            "municipality_id": self.municipality_id,
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "excerpt": self.excerpt(),
            "images": [get_image_url(image.image) for image in self.images.all()],
            "published_at": self.published_at,
            "attachment": get_file_url(self.attachment),
            "committee_id": self.committee_id,
            "score": sum(self.reactions.values_list("value", flat=True)),
            "category": self.category,
            "tags": [tag.name for tag in self.tags.all()],
            "hits": self.hits_count,
            # Backward compatibility
            "image": get_image_url(first_image.image) if first_image else None,
        }
        if user and user.is_authenticated:
            data["user_vote"] = sum(
                self.reactions.filter(user=user).values_list("value", flat=True)
            )
        return data

    def broadcast(self):
        """
        Sends a notification to each citizen, who's following the news
        of the mentioned municipality
            TODO: This could pontentially throttle for big enough user base
                Consider makeing it asynchronous, or switch to topic based notification
        TODO This is ugly, move it somewhere else
        """
        if self.municipality.can_broadcast():
            followers = self.municipality.citizens.all()
            notifications = [
                Notification(
                    user=follower.user,
                    title=self.title,
                    body=self.body,
                    subject_type=ContentType.objects.get_for_model(self),
                    municipality=self.municipality,
                )
                for follower in followers
            ]

            Notification.objects.bulk_create(notifications)
            self.municipality.set_last_broadcast(timezone.now())

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.to_broadcast:
                self.broadcast()
        super(News, self).save(*args, **kwargs)


class NewsImage(Model):
    image = models.ImageField(null=True, blank=True, upload_to="news/")
    news = models.ForeignKey("News", on_delete=CASCADE, related_name="images")


class NewsTag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Procedure(Model):
    municipality = models.ForeignKey(
        Municipality,
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name="procedures",
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    attachment = models.FileField(null=True, blank=True, upload_to="procedures/files/")
    display_order = models.IntegerField()
    type = models.CharField(
        max_length=50,
        choices=ProcedureTypes.get_choices(),
        default=ProcedureTypes.OTHER,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "procedures"
        verbose_name = "procedure"

    def to_dict(self):
        return {
            "municipality_id": self.municipality_id,
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "excerpt": self.body[:54] + " .. ",
            "display_order": self.display_order,
            "attachment": get_file_url(self.attachment),
            "type": self.type,
        }


class Report(CountableModel):
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="reports"
    )
    title = models.CharField(max_length=255)
    date = models.DateField()
    attachment = models.FileField(null=True, blank=True, upload_to="reports/files/")
    committee = models.ForeignKey(Committee, on_delete=CASCADE, related_name="reports")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "{}: {}".format(self.date, self.title)

    def to_dict(self):
        return {
            "created_at": self.created_at,
            "municipality_id": self.municipality_id,
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "attachment": get_file_url(self.attachment),
            "committee_id": self.committee_id,
            "hits": self.hits_count,
        }


class Event(Model):
    municipality = models.ForeignKey(
        Municipality, on_delete=CASCADE, related_name="events"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    starting_date = models.DateField()
    ending_date = models.DateField(null=True, blank=True)
    starting_time = models.TimeField(null=True, blank=True)
    ending_time = models.TimeField(null=True, blank=True)
    structure = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(null=True, blank=True, upload_to="events/")
    committees = models.ManyToManyField(Committee, related_name="events", blank=True)
    participants = models.ManyToManyField(Citizen, related_name="events", blank=True)
    interested_citizen = models.ManyToManyField(
        Citizen, related_name="events_interested_in", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notifications = GenericRelation(
        Notification,
        related_query_name="event",
        content_type_field="subject_type",
        object_id_field="subject_id",
    )

    @property
    @prefix_citizen_url
    def citizen_url(self):
        return f"event/{self.id}"

    def __str__(self):
        return "{}: {}-{}".format(self.title, self.starting_date, self.ending_date)

    def to_dict(self, user=None):
        data = {
            "municipality_id": self.municipality_id,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "starting_date": self.starting_date,
            "starting_time": self.starting_time,
            "ending_date": self.ending_date,
            "ending_time": self.ending_time,
            "structure": self.structure,
            "location": self.location,
            "image": get_image_url(self.image),
            "committees": list(self.committees.values_list("id", flat=True)),
            "number_of_participants": self.participants.count(),
            "number_of_interested_citizen": self.interested_citizen.count(),
            "created_at": self.created_at,
            # Backward compatibility
            "date": self.starting_date,
            "time": self.starting_time,
        }
        if user and is_citizen(user):
            data["user_interested"] = self.interested_citizen.filter(
                pk=user.citizen.pk
            ).exists()
            data["user_participating"] = self.participants.filter(
                pk=user.citizen.pk
            ).exists()
        return data

    class Meta:
        ordering = ["-created_at"]


class Association(Model):
    # User who submitted the Association creation request on ELbaladiya.tn
    created_by = models.ForeignKey(User, on_delete=CASCADE)
    full_name = models.CharField(max_length=120)
    full_name_arabic = models.CharField(max_length=120, null=True, blank=True)
    logo = models.ImageField(null=True, blank=True, upload_to="associations_logos/")
    description = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    contact_name = models.CharField(null=True, blank=True, max_length=60)
    contact_phone_number = models.CharField(null=True, blank=True, max_length=20)
    president_name = models.CharField(null=True, blank=True, max_length=60)
    president_phone_number = models.CharField(null=True, blank=True, max_length=20)
    email = models.EmailField(null=True, blank=True)
    jort_number = models.CharField(max_length=30, null=True, blank=True)
    jort_date = models.DateField(null=True, blank=True)
    facebook_page = models.CharField(max_length=255, null=True, blank=True)
    established_on = models.DateField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)
    partner_municipalities = models.ManyToManyField(
        Municipality, related_name="partner_associations", blank=True
    )

    def __str__(self):
        return self.full_name

    def to_dict(self):
        return {
            "full_name": self.full_name,
            "full_name_arabic": self.full_name_arabic,
            "logo": get_image_url(self.logo),
            "description": self.description,
            "website": self.website,
            "contact_name": self.contact_name,
            "contact_phone_number": self.contact_phone_number,
            "president_name": self.president_name,
            "president_phone_number": self.president_phone_number,
            "email": self.email,
            "jort_number": self.jort_number,
            "jort_date": self.jort_date,
            "facebook_page": self.facebook_page,
            "established_on": self.established_on,
            "additional_info": self.additional_info,
        }


class StaticText(Model):
    topic = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.topic

    def to_dict(self):
        return {"topic": self.topic, "title": self.title, "body": self.body}


class Appointment(Model):
    created_at = models.DateTimeField(auto_now_add=True)
    starting_date = models.DateTimeField()
    ending_date = models.DateTimeField()
    host = models.CharField(max_length=255)
    is_published = models.BooleanField()
    request_reception_message = models.CharField(max_length=1000)
    max_reservations = models.IntegerField()
    suggested_by = models.ForeignKey(
        "Manager", on_delete=CASCADE, related_name="suggested_appointments"
    )
    reviewed_by = models.ManyToManyField("Manager", related_name="appointments")

    def reservations_made(self):
        return sum(
            r.status()
            in [
                RequestStatus.RECEIVED,
                RequestStatus.PROCESSING,
                RequestStatus.ACCEPTED,
            ]
            for r in self.reservations.all()
        )

    def can_make_reservation(self):
        return self.reservations_made() < self.max_reservations


class Reservation(UpdatableModel):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    citizen = models.ForeignKey(
        "Citizen", on_delete=CASCADE, related_name="reservations"
    )
    appointment = models.ForeignKey(
        "Appointment", on_delete=CASCADE, related_name="reservations"
    )
    reservation_state_citizen = models.CharField(
        choices=RequestStatus.get_choices(),
        default=RequestStatus.ACCEPTED,
        max_length=255,
    )
    # This field represent reservation_state_host
    operation_updates = GenericRelation(
        "OperationUpdate", related_query_name="reservations"
    )
    notification_title = "رد على حجز موعد خاص بي"

    def status(self):
        if self.reservation_state_citizen == RequestStatus.REJECTED:
            return RequestStatus.REJECTED
        return super().status

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.appointment.can_make_reservation():
                super().save(*args, **kwargs)
                OperationUpdate.objects.create(
                    note="", status=RequestStatus.PROCESSING, operation=self
                )
                return True
            else:
                return False
        else:
            super().save(*args, **kwargs)

    @property
    def contact_number(self):
        return self.citizen.user.username

    @property
    def citizen_url(self):
        return ""


class Attachment(Model):
    file = models.FileField(upload_to="reservation/attachment/")
    reservation = models.ForeignKey(
        "Reservation", on_delete=CASCADE, related_name="attachments"
    )


class SMSBroadcastRequest(Model):
    municipality = models.ForeignKey(
        Municipality,
        on_delete=CASCADE,
        related_name="sms_broadcast_requests",
        blank=True,
        null=True,
    )
    # If this field is null, the SMSBroadcastRequest is created by the staff
    created_by = models.ForeignKey(
        Manager,
        on_delete=CASCADE,
        related_name="sms_broadcast_requests",
        blank=True,
        null=True,
    )
    status = models.CharField(
        choices=SMSBroadcastRequestStatus.get_choices(),
        max_length=255,
        default=SMSBroadcastRequestStatus.PENDING,
    )
    target = models.CharField(
        choices=SMSBroadcastRequestTarget.get_choices(), max_length=255
    )
    text = models.CharField(max_length=160)
    number_of_days = models.PositiveIntegerField(null=True, blank=True, default=None)
    scheduled_on = models.DateTimeField()

    def get_quantity(self):
        if self.target == SMSBroadcastRequestTarget.REGISTERED_CITIZENS:
            return self.municipality.citizens.count()
        if self.target == SMSBroadcastRequestTarget.FOLLOWING_CITIZENS:
            return self.municipality.starred_citizens.count()
        if self.target == SMSBroadcastRequestTarget.ALL_CITIZENS:
            return Citizen.objects.all().count()
        if self.target == SMSBroadcastRequestTarget.CUSTOM:
            return self.phone_numbers.count()
        if self.target == SMSBroadcastRequestTarget.INACTIVE_CITIZENS:
            if self.number_of_days is None:
                return Citizen.objects.filter(user__is_active=False).count()
            start_parsing_date = date.today() - timedelta(days=self.number_of_days)
            return Citizen.objects.filter(
                user__is_active=False, user__date_joined__gte=start_parsing_date
            ).count()

    def set_status(self, status):
        """
        SMS broadcast request should follow this following tansitions
        PENDING -> DECLINED, APPROVED
        APPROVED -> SENDING
        SENDING -> SENT
        DECLINED -> .
        """
        if status == SMSBroadcastRequestStatus.APPROVED:
            self.set_status_approved()

        if status == SMSBroadcastRequestStatus.DECLINED:
            self.set_status_declined()

        if status == SMSBroadcastRequestStatus.SENDING:
            self.set_status_sending()

        if status == SMSBroadcastRequestStatus.SENT:
            self.set_status_sent()

    def set_status_approved(self):
        if self.status == SMSBroadcastRequestStatus.PENDING:
            from backend.tasks import broadcast_sms

            broadcast_sms.apply_async([self.id], eta=self.scheduled_on)
            self.status = SMSBroadcastRequestStatus.APPROVED
        self.save()

    def set_status_declined(self):
        if self.status == SMSBroadcastRequestStatus.PENDING:
            self.status = SMSBroadcastRequestStatus.DECLINED
        self.save()

    def set_status_sending(self):
        if self.status == SMSBroadcastRequestStatus.APPROVED:
            self.status = SMSBroadcastRequestStatus.SENDING
        self.save()

    def set_status_sent(self):
        if self.status == SMSBroadcastRequestStatus.SENDING:
            self.status = SMSBroadcastRequestStatus.SENT
        self.save()

    def is_approved(self):
        return self.status == SMSBroadcastRequestStatus.APPROVED

    def is_created_by_staff(self):
        return self.created_by is None


class SMSBroadCastPhoneNumber(models.Model):
    number = models.CharField(max_length=8)
    sms_broadcast_request = models.ForeignKey(
        "SMSBroadcastRequest", on_delete=CASCADE, related_name="phone_numbers"
    )
