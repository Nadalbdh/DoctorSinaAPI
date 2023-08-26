from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from backend.decorators import IsValidGenericApi
from backend.mixins import GetCollectionMixin, GetObjectMixin
from backend.models import NewsTag


# News Tag Getters
@IsValidGenericApi()
class NewsTagView(GetObjectMixin, GenericAPIView):
    permission_classes = [AllowAny]
    model = NewsTag


@IsValidGenericApi()
class NewsTagsView(GetCollectionMixin, GenericAPIView):
    permission_classes = [AllowAny]
    model = NewsTag
