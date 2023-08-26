from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from backend.decorators import IsValidGenericApi
from backend.mixins import GetCollectionMixin, GetObjectMixin
from backend.models import Association


# Associations Getters
@IsValidGenericApi()
class AssociationView(GetObjectMixin, GenericAPIView):
    permission_classes = [AllowAny]
    model = Association


@IsValidGenericApi()
class AssociationsView(GetCollectionMixin, GenericAPIView):
    permission_classes = [AllowAny]
    model = Association
