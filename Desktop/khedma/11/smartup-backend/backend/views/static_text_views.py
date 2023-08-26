from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from backend.decorators import IsValidGenericApi
from backend.mixins import GetCollectionMixin, GetObjectMixin
from backend.models import StaticText


# Static Texts Getters
@IsValidGenericApi()
class StaticTextView(GetObjectMixin, GenericAPIView):
    permission_classes = [AllowAny]
    model = StaticText


@IsValidGenericApi()
class StaticTextsView(GetCollectionMixin, GenericAPIView):
    permission_classes = [AllowAny]
    model = StaticText
