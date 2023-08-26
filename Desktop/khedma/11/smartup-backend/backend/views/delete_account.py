from datetime import datetime

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import Citizen, Manager, Municipality
from backend.services.delete_account import delete_account
from settings.custom_permissions import MunicipalityManagerPermission


class DeleteAccount(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=self.request.user.pk)
        delete_account(user)
        return Response({"message": "User Deleted Successfully"}, status=204)


class DeleteManagerAccount(APIView):
    permission_classes = [IsAuthenticated & MunicipalityManagerPermission]

    def delete(self, request, municipality_id, manager_id, *args, **kwargs):
        manager = get_object_or_404(Manager, id=manager_id)
        user = manager.user
        if not request.user.has_perm(
            "MANAGE_PERMISSIONS", get_object_or_404(Municipality, id=municipality_id)
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)
        delete_account(user)
        return Response({"message": "User Deleted Successfully"}, status=204)
