import re
from datetime import datetime

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from backend.decorators import only_managers, request_user_field
from backend.enum import (
    DossierTypes,
    ForumTypes,
    GenderType,
    NewsCategory,
    ProcedureTypes,
    ReactionPostsTypes,
    ReactionsTypes,
    RequestStatus,
    ResetPasswordTypes,
)
from backend.functions import (
    convert_base64_to_file,
    convert_base64_to_image,
    get_image_url,
    is_municipality_manager,
)
from backend.helpers import get_unique_identifier
from backend.models import (
    Appointment,
    Attachment,
    Building,
    Citizen,
    Comment,
    Complaint,
    ComplaintCategory,
    ComplaintSubCategory,
    Dossier,
    DossierAttachment,
    Event,
    Municipality,
    News,
    NewsImage,
    NewsTag,
    OperationUpdate,
    Procedure,
    Region,
    Report,
    Reservation,
    SMSBroadCastPhoneNumber,
    SMSBroadcastRequest,
    SubjectAccessRequest,
    Topic,
)
from backend.serializers.fields import Base64FileField, ImageField
from backend.validators import validate_digits

from .default_serializer import (
    convert_to_image,
    DefaultSerializer,
    validator_string_is_base_64_img,
)


class PhoneNumberField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(min_length=8, max_length=8, *args, **kwargs)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        validate_digits(data, serializers.ValidationError)
        return data


class HasFollowersSerializer(serializers.ModelSerializer):
    followers = serializers.SerializerMethodField(read_only=True)

    def get_followers(self, obj):
        return list(obj.followers.all().values_list("id", flat=True))


class RegisterSerializer(DefaultSerializer):
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    # phone_number is saved in User.username field
    phone_number = PhoneNumberField()
    password = serializers.CharField(min_length=1, allow_blank=True)
    birth_date = serializers.DateField(required=False)
    municipality_id = serializers.IntegerField(min_value=1)
    gender = serializers.ChoiceField(
        choices=GenderType.get_choices(), default=GenderType.MALE
    )

    def create(self, validated_data):
        municipality = Municipality.objects.get(pk=validated_data["municipality_id"])
        user, first_sign_up = User.objects.get_or_create(
            username=validated_data["phone_number"]
        )
        if first_sign_up:
            user.password = make_password(validated_data["password"])
            user.first_name = validated_data["first_name"].capitalize()
            user.last_name = validated_data["last_name"].capitalize()
            user.is_active = False
            user.save()
            citizen = Citizen.objects.create(
                user=user,
                birth_date=validated_data.get("birth_date"),
                gender=validated_data.get("gender"),
                preferred_municipality=municipality,
                registration_municipality=municipality,
            )
            citizen.municipalities.add(municipality)
        return municipality, user


class VerifyOTPSerializer(DefaultSerializer):
    phone_number = PhoneNumberField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def update(self, user, validated_data):
        user.is_active = True
        user.save()


class ResetPasswordSerializer(DefaultSerializer):
    type = serializers.ChoiceField(choices=ResetPasswordTypes.get_choices())
    phone_number = PhoneNumberField()


class ChangePasswordSerializer(DefaultSerializer):
    new_password = serializers.CharField()
    old_password = serializers.CharField(required=False)  # optional old_password check


class EditProfileSerializer(DefaultSerializer):
    cin_number = serializers.CharField(
        max_length=8, required=False, allow_null=True, allow_blank=True
    )
    function = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=255
    )
    birth_date = serializers.DateField(required=False, allow_null=True)
    facebook_account = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    first_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    preferred_municipality_id = serializers.IntegerField(
        required=False, allow_null=True
    )
    registration_municipality_id = serializers.IntegerField(
        required=False, allow_null=True
    )
    profile_picture = serializers.CharField(
        required=False, validators=[validator_string_is_base_64_img], allow_blank=True
    )
    gender = serializers.ChoiceField(
        choices=GenderType.get_choices(), default=GenderType.MALE
    )

    def update(self, citizen, validated_data):
        citizen.cin_number = validated_data.get("cin_number", citizen.cin_number)
        citizen.function = validated_data.get("function", citizen.function)
        citizen.birth_date = validated_data.get("birth_date", citizen.birth_date)
        citizen.facebook_account = validated_data.get(
            "facebook_account", citizen.facebook_account
        )
        citizen.address = validated_data.get("address", citizen.address)
        citizen.preferred_municipality_id = validated_data.get(
            "preferred_municipality_id", citizen.preferred_municipality_id
        )
        citizen.registration_municipality_id = validated_data.get(
            "registration_municipality_id", citizen.registration_municipality_id
        )

        citizen.gender = validated_data.get("gender", citizen.gender)

        if validated_data.get("profile_picture"):
            citizen.profile_picture = convert_to_image(
                validated_data["profile_picture"], citizen.user.get_full_name()
            )
        citizen.user.email = validated_data.get("email", citizen.user.email)
        citizen.user.first_name = validated_data.get(
            "first_name", citizen.user.first_name
        )
        citizen.user.last_name = validated_data.get("last_name", citizen.user.last_name)
        citizen.user.save()
        citizen.save()
        return citizen


class OperationUpdateCRUDSerializer(serializers.ModelSerializer):
    image = ImageField(allow_null=True, required=False)

    class Meta:
        model = OperationUpdate
        fields = ("image",)


class OperationUpdateSerializer(serializers.ModelSerializer):
    date = serializers.ReadOnlyField(source="created_at")
    image = ImageField(required=False, read_only=True)

    class Meta:
        model = OperationUpdate
        fields = [
            "id",
            "note",
            "status",
            "created_by",
            "date",
            "created_by_name",
            "image",
        ]


class SubjectAccessRequestSerializer(HasFollowersSerializer):
    # DEPRECATED START
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="created_by"
    )
    ref = serializers.ReadOnlyField(source="reference")
    remarque = serializers.ReadOnlyField(source="note")
    # END
    attachment = Base64FileField(required=False, allow_null=True)
    updates = OperationUpdateSerializer(
        source="operation_updates", many=True, read_only=True
    )
    hits = serializers.ReadOnlyField(source="hits_count")
    user_address = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_fullname = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()
    image = ImageField(required=False)

    class Meta:
        model = SubjectAccessRequest
        fields = "__all__"
        read_only_fields = ["created_at", "created_by"]

    @only_managers()
    def get_user_address(self, obj):
        return obj.created_by.citizen.address

    @only_managers(default="")
    def get_user_fullname(self, obj):
        return obj.created_by.get_full_name()

    @only_managers(default="")
    def get_user_email(self, obj):
        return obj.created_by.email

    @only_managers()
    def get_user_phone(self, obj):
        return obj.created_by.username


class SubCategoryField(serializers.SlugRelatedField):
    def __init__(self, **kwargs):
        super().__init__(slug_field="name", **kwargs)

    def get_queryset(self):
        data = self.root.initial_data
        if "category" in data:
            return ComplaintSubCategory.objects.filter(category__name=data["category"])
        if "id" in data:
            try:
                instance = Complaint.objects.get(pk=data["id"])
                if instance.category is not None:
                    return ComplaintSubCategory.objects.filter(
                        category__name=instance.category.name
                    )
            except ObjectDoesNotExist as error:
                raise ValidationError("Matching Category does not exist") from error
        return ComplaintSubCategory.objects.all()


class ComplaintSerializer(HasFollowersSerializer):
    image = ImageField(required=False)
    category = serializers.SlugRelatedField(
        slug_field="name", queryset=ComplaintCategory.objects.all(), allow_null=True
    )
    region = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Region.objects.all(),
        required=False,
        allow_null=True,
    )
    sub_category = SubCategoryField(required=False, allow_null=True)
    hits = serializers.ReadOnlyField(source="hits_count")
    contact_number = serializers.SerializerMethodField()
    score = serializers.ReadOnlyField()
    created_by = serializers.ReadOnlyField(source="created_by_username")
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="created_by"
    )
    updates = OperationUpdateSerializer(
        source="operation_updates", many=True, read_only=True
    )
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = "__all__"
        read_only_fields = ["created_at"]

    @request_user_field()
    def get_contact_number(self, obj, user):
        if is_municipality_manager(user=user, municipality_id=obj.municipality.id):
            return obj.contact_number
        return None

    @request_user_field(default=0)
    def get_user_vote(self, obj, user):
        if not user.is_anonymous:
            return obj.user_vote(user)
        return 0


class BuildingSerializer(serializers.ModelSerializer):
    image = ImageField(required=False)

    class Meta:
        model = Building
        fields = "__all__"


class DossierAttachmentSerializer(serializers.ModelSerializer):
    attachment = Base64FileField(required=False, allow_null=True)
    image = ImageField(required=False)

    class Meta:
        model = DossierAttachment
        fields = "__all__"


class DossierSerializer(HasFollowersSerializer):
    created_by = serializers.ReadOnlyField(source="created_by_username")
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="created_by"
    )
    updates = OperationUpdateSerializer(
        source="operation_updates", many=True, read_only=True
    )
    phone_number = PhoneNumberField(required=False)
    attachments = DossierAttachmentSerializer(many=True, read_only=True)
    building = BuildingSerializer(read_only=True)
    image = ImageField(required=False, allow_null=True)
    unique_identifier = serializers.CharField(
        max_length=20, required=False, allow_null=True
    )

    class Meta:
        model = Dossier
        fields = "__all__"

    def create(self, validated_data):
        if validated_data.get("unique_identifier") is None:
            validated_data["unique_identifier"] = get_unique_identifier(Dossier)
        dossier = Dossier.objects.create(**validated_data)
        return dossier


class CustomUpdateStatusSerializer(DefaultSerializer):
    status = serializers.ChoiceField(choices=RequestStatus.get_choices())
    note = serializers.CharField(allow_blank=True, default="")
    id = serializers.IntegerField()
    image = ImageField(required=False)

    def create(self, validated_data):
        return OperationUpdate(
            image=validated_data["image"] if "image" in validated_data else None,
            status=validated_data["status"],
            note=validated_data["note"],
            object_id=validated_data["id"],
            created_by=validated_data["created_by"],
        )

    def update(self, instance, validated_data):
        operation_update = self.create(validated_data)
        operation_update.operation = instance
        operation_update.save()
        return operation_update.operation


class UpdateStatusSerializer(DefaultSerializer):
    status = serializers.ChoiceField(choices=RequestStatus.get_choices())
    note = serializers.CharField(allow_blank=True, default="")
    image = ImageField(required=False)


class ReportCreateSerializer(DefaultSerializer):
    title = serializers.CharField(max_length=255)
    date = serializers.DateField(default=timezone.now)
    attachment = serializers.CharField(required=False)
    committee_id = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        if validated_data.get("attachment"):
            validated_data["attachment"] = ReportUpdateSerializer.convert_to_file(
                validated_data["attachment"], validated_data.get("title")
            )
        return Report.objects.create(**validated_data)


class ReportUpdateSerializer(DefaultSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, required=False)
    date = serializers.DateField(default=timezone.now)
    attachment = serializers.CharField(required=False)
    committee_id = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )

    @staticmethod
    def convert_to_file(base_64_file, title):
        return convert_base64_to_file(
            base_64_file, "{}_{}".format(title, timezone.now())
        )


class ProcedureCreateSerializer(DefaultSerializer):
    title = serializers.CharField(max_length=200)
    body = serializers.CharField()
    display_order = serializers.IntegerField()
    attachment = serializers.CharField(required=False)
    type = serializers.ChoiceField(
        choices=ProcedureTypes.get_choices(), default=ProcedureTypes.OTHER
    )

    def create(self, validated_data):
        if validated_data.get("attachment"):
            validated_data["attachment"] = ProcedureUpdateSerializer.convert_to_file(
                validated_data["attachment"], validated_data.get("title")
            )
        return Procedure.objects.create(**validated_data)


class ProcedureUpdateSerializer(DefaultSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=200, required=False)
    body = serializers.CharField(required=False)
    display_order = serializers.IntegerField(required=False)
    attachment = serializers.CharField(required=False)
    type = serializers.ChoiceField(
        choices=ProcedureTypes.get_choices(), default=ProcedureTypes.OTHER
    )

    @staticmethod
    def convert_to_file(base_64_file, title):
        return convert_base64_to_file(
            base_64_file, "{}_{}".format(title, timezone.now())
        )


class NewsCreateSerializer(DefaultSerializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    published_at = serializers.DateTimeField(required=False, default=datetime.now())
    images = serializers.ListField(
        required=False,
        child=serializers.CharField(validators=[validator_string_is_base_64_img]),
    )
    attachment = serializers.CharField(required=False)
    committee_id = serializers.IntegerField(required=False, allow_null=True)
    to_broadcast = serializers.BooleanField(default=False)
    category = serializers.ChoiceField(
        choices=NewsCategory.get_choices(), default=NewsCategory.ANNOUNCEMENT
    )
    tags = serializers.ListField(required=False, child=serializers.CharField())

    def create(self, validated_data):
        images = []
        if "images" in validated_data:
            images = validated_data.pop("images")

        tags = []
        if "tags" in validated_data:
            tags = validated_data.pop("tags")

        if "attachment" in validated_data:
            validated_data["attachment"] = NewsUpdateSerializer.convert_to_file(
                validated_data["attachment"], validated_data.get("title")
            )

        news = News.objects.create(**validated_data)

        NewsImage.objects.bulk_create(
            [
                NewsImage(
                    news=news,
                    image=NewsUpdateSerializer.convert_to_image(
                        image, validated_data.get("title")
                    ),
                )
                for image in images
            ]
        )

        tags = NewsTag.objects.filter(name__in=tags)

        news.tags.set(tags)

        return news


class NewsUpdateSerializer(DefaultSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, required=False)
    body = serializers.CharField(required=False)
    published_at = serializers.DateTimeField(required=False)
    images = serializers.ListField(
        required=False,
        child=serializers.CharField(validators=[validator_string_is_base_64_img]),
    )
    attachment = serializers.CharField(required=False)
    committee_id = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(required=False, child=serializers.CharField())
    category = serializers.ChoiceField(
        choices=NewsCategory.get_choices(), required=False
    )

    @staticmethod
    def convert_to_image(base_64_image, title):
        return convert_base64_to_image(
            base_64_image, "{}_{}".format(title, timezone.now())
        )

    @staticmethod
    def convert_to_file(base_64_file, title):
        return convert_base64_to_file(
            base_64_file, "{}_{}".format(title, timezone.now())
        )

    def update(self, instance, validated_data):
        images = None
        if "images" in validated_data:
            images = validated_data.pop("images")

        tags = None
        if "tags" in validated_data:
            tags = validated_data.pop("tags")

        if "attachment" in validated_data:
            validated_data["attachment"] = NewsUpdateSerializer.convert_to_file(
                validated_data["attachment"], validated_data.get("title")
            )

        news = super().update(instance, validated_data)

        if images is not None:
            news.images.all().delete()
            NewsImage.objects.bulk_create(
                [
                    NewsImage(
                        news=news,
                        image=NewsUpdateSerializer.convert_to_image(image, news.title),
                    )
                    for image in images
                ]
            )

        if tags is not None:
            tags = NewsTag.objects.filter(name__in=tags)
            news.tags.set(tags)

        return news


class EventCreateSerializer(DefaultSerializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    starting_date = serializers.DateField()
    ending_date = serializers.DateField(required=False)
    starting_time = serializers.TimeField(required=False)
    ending_time = serializers.TimeField(required=False)
    structure = serializers.CharField(max_length=255, required=False)
    location = serializers.CharField(max_length=255, required=False)
    image = serializers.CharField(
        required=False, validators=[validator_string_is_base_64_img]
    )
    committees = serializers.ListField(child=serializers.IntegerField(), required=False)

    def create(self, validated_data):
        if validated_data.get("image"):
            validated_data["image"] = EventUpdateSerializer.convert_to_image(
                validated_data["image"], validated_data.get("title")
            )
        committees = validated_data.pop("committees", [])
        events = Event.objects.create(**validated_data)
        events.committees.set(committees)
        return events


class EventUpdateSerializer(DefaultSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False)
    starting_date = serializers.DateField(required=False)
    ending_date = serializers.DateField(required=False)
    starting_time = serializers.TimeField(required=False)
    ending_time = serializers.TimeField(required=False)
    structure = serializers.CharField(max_length=255, required=False)
    location = serializers.CharField(max_length=255, required=False)
    image = serializers.CharField(
        required=False, validators=[validator_string_is_base_64_img]
    )
    committees = serializers.ListField(child=serializers.IntegerField(), required=False)

    @staticmethod
    def convert_to_image(base_64_image, title):
        return convert_base64_to_image(
            base_64_image, "{}_{}".format(title, timezone.now())
        )

    def update(self, instance, validated_data):
        committees = validated_data.pop("committees", [])
        instance.committees.set(committees)
        return super().update(instance, validated_data)


class EventParticipateSerializer(DefaultSerializer):
    participate = serializers.BooleanField(required=False)


# DEPRECATED, use EventParticipateSerializer with "participate":False instead
class EventUnparticipateSerializer(DefaultSerializer):
    id = serializers.IntegerField()


class EventInterestSerializer(DefaultSerializer):
    interest = serializers.BooleanField(required=False)


# DEPRECATED, use EventDisinterestSerializer with "interest":False instead
class EventDisinterestSerializer(DefaultSerializer):
    id = serializers.IntegerField()


class CommentCreateSerializer(DefaultSerializer):
    created_by = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    created_at = serializers.DateTimeField(required=False)
    committee_id = serializers.IntegerField(required=False, allow_null=True)
    image = serializers.CharField(
        required=False, validators=[validator_string_is_base_64_img]
    )
    parent_comment_id = serializers.IntegerField(required=False, allow_null=True)
    topic = PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False)
    type = serializers.ChoiceField(choices=ForumTypes.get_choices(), required=False)

    def create(self, validated_data):
        if validated_data.get("image"):
            validated_data["image"] = CommentUpdateSerializer.convert_to_image(
                validated_data["image"], validated_data.get("title")
            )
        if "parent_comment_id" in validated_data:
            parent_comment = Comment.objects.get(pk=validated_data["parent_comment_id"])
            validated_data["municipality_id"] = parent_comment.municipality_id
            validated_data["committee_id"] = parent_comment.committee_id
        return Comment.objects.create(**validated_data)


class CommentUpdateSerializer(DefaultSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255, required=False)
    body = serializers.CharField(required=False)
    image = serializers.CharField(
        required=False, validators=[validator_string_is_base_64_img]
    )
    topic = PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False)
    type = serializers.ChoiceField(choices=ForumTypes.get_choices(), required=False)

    @staticmethod
    def convert_to_image(base_64_image, title):
        return convert_base64_to_image(
            base_64_image, "{}_{}".format(title, timezone.now())
        )


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"
        read_only_fields = ["created_at"]


class ReactionSerializer(DefaultSerializer):
    type = serializers.ChoiceField(
        choices=ReactionsTypes.get_choices(), default=ReactionsTypes.LIKE
    )
    value = serializers.IntegerField()
    post_type = serializers.ChoiceField(choices=ReactionPostsTypes.get_choices())
    post_id = serializers.IntegerField()

    @staticmethod
    def get_class_from_post_type(post_type):
        post_classes = {
            ReactionPostsTypes.COMMENT: Comment,
            ReactionPostsTypes.NEWS: News,
            ReactionPostsTypes.COMPLAINT: Complaint,
        }
        return post_classes[post_type]

    def create(self, validated_data):
        post_class = ReactionSerializer.get_class_from_post_type(
            validated_data.pop("post_type")
        )
        post = post_class.objects.get(pk=validated_data.pop("post_id"))
        try:
            existing_reaction = post.reactions.get(user=validated_data["user_id"])
        except ObjectDoesNotExist:
            return post.reactions.create(**validated_data)
        existing_reaction.value = validated_data["value"]
        if existing_reaction.value == 0:
            existing_reaction.delete()
        else:
            existing_reaction.save()


class RegionCreateSerializer(DefaultSerializer):
    name = serializers.CharField(max_length=30)

    def create(self, validated_data):
        return Region.objects.create(**validated_data)


class RegionUpdateSerializer(DefaultSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=30)

    def update(self, instance, validated_data):
        instance.name = validated_data["name"]
        instance.save()
        return instance


class AppointmentSerializer(serializers.ModelSerializer):
    reservations_made = serializers.ReadOnlyField()

    class Meta:
        model = Appointment
        fields = "__all__"


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"


class ReservationSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField()
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"

    def validate(self, data):
        # Be careful of partial updates
        if "appointment" in data and not data["appointment"].can_make_reservation():
            raise ValidationError(
                "No more reservation can be done for this appointment"
            )
        return super().validate(data)


class SMSBroadCastPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSBroadCastPhoneNumber
        fields = ["number"]

    def validate(self, data):
        is_valid = bool(re.match(r"^[234759]\d{7}$", data["number"]))
        if not is_valid:
            raise ValidationError("Phone number is not valid")
        return super().validate(data)


class SMSBroadcastRequestSerializer(serializers.ModelSerializer):
    phone_numbers = SMSBroadCastPhoneNumberSerializer(required=False, many=True)

    class Meta:
        model = SMSBroadcastRequest
        fields = "__all__"
        extra_fields = ["phone_numbers"]

    def create(self, validated_data):
        phone_numbers = validated_data.pop("phone_numbers", [])
        sms_broadcast_request = SMSBroadcastRequest.objects.create(**validated_data)
        SMSBroadCastPhoneNumber.objects.bulk_create(
            [
                SMSBroadCastPhoneNumber(
                    sms_broadcast_request=sms_broadcast_request, **phone_number
                )
                for phone_number in phone_numbers
            ]
        )
        return sms_broadcast_request

    def to_representation(self, instance):
        rep = super(SMSBroadcastRequestSerializer, self).to_representation(instance)
        updates = None
        if instance.is_created_by_staff():
            # Special requests, created by the staff.
            updates = {
                "municipality": "Baladiya.tn"
                if instance.municipality is None
                else str(instance.municipality),
                "created_by": "STAFF",
                "quantity": instance.get_quantity(),
                "municipality_sms_credit": "",
                "municipality_total_sms_consumption": "",
                "last_sms_broadcast": "",
                "scheduled_on": instance.scheduled_on.strftime("%Y-%m-%dT%H:%M"),
            }
        else:
            last_sms_broadcast = instance.municipality.last_sms_broadcast()
            updates = {
                "municipality": str(instance.municipality),
                "created_by": str(instance.created_by),
                "quantity": instance.get_quantity(),
                "municipality_sms_credit": instance.municipality.sms_credit,
                "municipality_total_sms_consumption": instance.municipality.total_sms_consumption,
                "last_sms_broadcast": "Never"
                if last_sms_broadcast is None
                else last_sms_broadcast.scheduled_on,
                "scheduled_on": instance.scheduled_on.strftime("%Y-%m-%dT%H:%M"),
            }
        rep.update(updates)
        return rep


class MunicipalityFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = (
            "service_eticket",
            "service_dossiers",
            "service_complaints",
            "service_sar",
            "service_procedures",
            "service_news",
            "service_forum",
            "service_reports",
            "service_events",
        )


class MunicipalitySerializer(serializers.ModelSerializer):
    route_name = serializers.ReadOnlyField(source="get_route_name")
    total_followers = serializers.ReadOnlyField(source="total_followed")
    total_managers = serializers.ReadOnlyField(source="managers_count")
    logo = ImageField(required=False)

    class Meta:
        model = Municipality
        fields = "__all__"
        read_only_fields = (
            "name",
            "name_fr",
            "city",
            "is_active",
            "is_signed",
            "latitude",
            "longitude",
            "sms_credit",
            "population",
            "total_sms_consumption",
            "has_eticket",
            "activation_date",
            "service_eticket",
            "service_dossiers",
            "service_complaints",
            "service_sar",
            "service_procedures",
            "service_news",
            "service_forum",
            "service_reports",
            "service_events",
            "sms_credit",
            "broadcast_frequency",
            "last_broadcast",
            "route_name",
            "total_followers",
            "total_managers",
        )


class MunicipalityMetadataSerializer(serializers.ModelSerializer):
    route_name = serializers.ReadOnlyField(source="get_route_name")
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Municipality
        fields = (
            "id",
            "name",
            "name_fr",
            "city",
            "is_active",
            "is_signed",
            "has_eticket",
            "logo",
            "longitude",
            "latitude",
            "route_name",
            "activation_date",
        )

    def get_logo(self, obj):
        return get_image_url(obj.logo)

    def get_route_name(self, obj):
        return obj.get_route_name()
