from rest_framework.generics import GenericAPIView
from rest_framework.mixins import UpdateModelMixin

from backend.models import OperationUpdate
from backend.serializers.serializers import OperationUpdateCRUDSerializer
from settings.custom_permissions import MunicipalityManagerWriteOnlyPermission


class OperationUpdateViewSet(GenericAPIView, UpdateModelMixin):
    permission_classes = [MunicipalityManagerWriteOnlyPermission]
    queryset = OperationUpdate.objects.all()
    serializer_class = OperationUpdateCRUDSerializer
    lookup_url_kwarg = "id"

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
