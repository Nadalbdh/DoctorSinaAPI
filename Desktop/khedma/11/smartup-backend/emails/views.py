from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView

from backend.decorators import IsValidGenericApi
from backend.mixins import CRUDCollectionMixin, CRUDObjectMixin
from backend.models import Municipality
from emails.helpers.mailing_list import update_mailing_list
from emails.models import Email
from emails.serializers import EMailSerializer, MailingListSerializer


@IsValidGenericApi()
class MailingListView(GenericAPIView):
    serializer_class = MailingListSerializer

    def post(self, request, serializer, municipality_id):
        emails = serializer.validated_data["emails"]
        municipality = get_object_or_404(Municipality, pk=municipality_id)
        update_mailing_list(municipality, emails)
        return HttpResponse(status=status.HTTP_201_CREATED)

    def get(self, request, municipality_id):
        municipality = get_object_or_404(Municipality, pk=municipality_id)
        emails = list(municipality.summary_email_list())
        return JsonResponse(data={"emails": emails}, status=status.HTTP_200_OK)


@IsValidGenericApi()
class EMailView(CRUDObjectMixin, GenericAPIView):
    model = Email
    serializer_class = EMailSerializer


@IsValidGenericApi()
class EMailsView(CRUDCollectionMixin, GenericAPIView):
    model = Email
    serializer_class = EMailSerializer
