import os
from io import BufferedWriter

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import FileResponse, Http404, HttpResponse
from docxtpl import DocxTemplate
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from backend.exceptions import NotOwner
from backend.functions import get_citizen_from_request, is_municipality_manager
from backend.models import Hit, OperationUpdate
from backend.serializers.serializers import UpdateStatusSerializer


class BaseViewMixin:
    model = None

    def to_dict(self, obj, **kwargs):
        """
        Returns a dictionary representation of the object
        """
        if hasattr(obj, "to_dict"):
            # Note: some models do not accept anything as an argument, and thus will fail.
            # This solves the problem in a quick-and-dirty way, without touching the models
            try:
                return obj.to_dict(**kwargs)
            except TypeError:
                return obj.to_dict()
        return model_to_dict(obj)

    def get_queryset(self, **kwargs):
        if "municipality_id" in kwargs:
            return self.model.objects.filter(municipality_id=kwargs["municipality_id"])
        return self.model.objects.all()

    def get_object(self, **kwargs):
        queryset = self.get_queryset(**kwargs)
        try:
            return queryset.get(**kwargs)
        except ObjectDoesNotExist as exception:
            raise Http404(
                "No %s matches the given query." % queryset.model._meta.object_name
            ) from exception


class GetObjectMixin(BaseViewMixin):
    def get(self, request, **kwargs):
        obj = self.get_object(**kwargs)
        return Response(data=self.to_dict(obj, user=request.user))


class CountableObjectMixin:
    """
    Increment hits for after retrieving a model instance.
    Note: Should be before CRUDObjectMixin (or any mixin that overrides
    the get method) on the inheritance list.
    """

    def get(self, request, **kwargs):
        obj = self.get_object(**kwargs)
        Hit.objects.create(citizen=get_citizen_from_request(request), object=obj)
        return Response(data=self.to_dict(obj, user=request.user))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Hit.objects.create(citizen=get_citizen_from_request(request), object=instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UpdateObjectMixin(BaseViewMixin):
    def put(self, request, serializer, **kwargs):
        """
        Updates and returns object
        return codes:
            - 200: element updated successfully
            - 404: element not found
        """
        obj = self.get_object(**kwargs)
        obj = serializer.update(obj, serializer.validated_data)
        return Response(data=self.to_dict(obj, user=request.user))


class DeleteObjectMixin(BaseViewMixin):
    def delete(self, request, **kwargs):
        """
        Deletes an object
        return codes:
            - 200: element deleted successfully
            - 204: element des not exist already
        """
        obj = self.get_object(**kwargs)
        obj.delete()
        return HttpResponse(status=status.HTTP_200_OK)


class CRUDObjectMixin(GetObjectMixin, UpdateObjectMixin, DeleteObjectMixin):
    pass


class PrivacyMixin:
    """
    Adds a privacy check to the queryset. Only return objects
    if the user is a manager, or if they're created by the
    same user, or if they're public.
    """

    def get_queryset(self, **kwargs):
        municipality_id = kwargs.get("municipality") or kwargs.get("municipality_id")
        base_queryset = super().get_queryset(**kwargs)
        user = self.request.user
        if is_municipality_manager(user, municipality_id):
            return base_queryset
        if user.is_anonymous:
            return base_queryset.filter(Q(is_public=True))
        return base_queryset.filter(Q(created_by=user) | Q(is_public=True))


class PrivateOnlyMixin:
    """
    Handles a get parameter to only return the objects
    created by the request user
    """

    def get_queryset(self):
        base_queryset = super().get_queryset()

        if self.request.GET.get("private_only") == "True":
            return base_queryset.filter(created_by=self.request.user)

        return base_queryset


class GetCollectionMixin(BaseViewMixin):
    def do_paging(self, objects, request):
        page = request.GET.get("page", 1)
        per_page = request.GET.get("per_page", 10)
        paginator = Paginator(objects, per_page)

        try:
            return paginator.page(page)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return []

    def get(self, request, **kwargs):
        """
        Returns all objects
            - Optional argument: private_only=True => return objects created by current user only
            - Optional Keyword Argument: municipality_id => filter by specific municipality_id
        """
        objects = self.get_queryset(**kwargs)

        if request.GET.get("private_only") == "True":
            objects = objects.filter(created_by=request.user)

        if "page" in request.GET or "per_page" in request.GET:
            objects = self.do_paging(objects, request)

        collection = [self.to_dict(obj, user=request.user) for obj in objects]
        return Response(data=collection)


class CreateObjectMixin(BaseViewMixin):
    def post(self, request, serializer, **kwargs):
        """
        Creates and returns object
        return codes:
            - 201: element created successfully
        """
        if "municipality_id" in kwargs:
            serializer.validated_data["municipality_id"] = kwargs["municipality_id"]
            obj = serializer.create(serializer.validated_data)
        else:
            obj = serializer.create(serializer.validated_data)
        return Response(
            data=self.to_dict(obj, user=request.user), status=status.HTTP_201_CREATED
        )


class CRUDCollectionMixin(GetCollectionMixin, CreateObjectMixin):
    pass


class UpdateStatusMixin:
    notification_title = None

    def post(self, request, serializer, **kwargs):
        """
        Updates status and returns object with object updates
        return codes:
            - 200: element updated successfully
            - 404: element not found
        """
        obj = self.model.objects.get(pk=serializer.validated_data["id"])
        # This would be best added to get_serializer, but it doesn't work because of IsValidGenericApi
        serializer.validated_data["created_by"] = request.user
        obj = serializer.update(obj, serializer.validated_data)
        return Response(data=self.to_dict(obj, user=request.user))

    def create_operation_update(self, request, data, instance):
        image = data["image"] if "image" in data else None
        return OperationUpdate.objects.create(
            status=data["status"],
            note=data["note"],
            image=image,
            created_by=request.user,
            operation=instance,
        )

    def update_status(self, request, *args, **kwargs):
        """
        Updates status and returns object with object updates
        return codes:
            - 200: element updated successfully
            - 404: element not found
        """
        instance = self.get_object()
        update_serializer = UpdateStatusSerializer(data=request.data)
        update_serializer.is_valid(raise_exception=True)
        update = self.create_operation_update(
            request, update_serializer.validated_data, instance
        )
        serializer = self.get_serializer(update.operation)
        return Response(serializer.data)


class ElBaladiyaGenericViewSet(viewsets.GenericViewSet):
    """
    A custom GenericViewSet, that mainly does two things:
      - Filters the queryset based on the url
      - Adds the url parameters to the serializer
    """

    model = None

    # Provide a generic get_queryset: use the
    # kwargs to filter.
    def get_queryset(self):
        return self.model.objects.filter(**self.kwargs)

    # Override any kwargs set in the request data,
    # that are also set in the URL.
    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            kwargs["data"].update(self.kwargs)
        return super().get_serializer(*args, **kwargs)


class SetCreatedByMixin:
    def create(self, request, *args, **kwargs):
        # small hack to set missing fields
        if type(request.data) != dict:
            request.data._mutable = True

        request.data["created_by_id"] = request.user.pk
        request.data["created_by"] = request.user.pk
        return super().create(request, *args, **kwargs)


class ElBaladiyaPermissionViewSetMixin(AutoPermissionViewSetMixin):
    permission_type_map = {
        **AutoPermissionViewSetMixin.permission_type_map,
        "update_status": "opupdate",
    }


class ElBaladiyaModelViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    ElBaladiyaGenericViewSet,
):
    pass


class ElBaladiyaNestedModelViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    model = None

    def get_queryset(self):
        return self.model.objects.all()


class CreateDossierRelatedModelMixin:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_by = serializer.validated_data.get("dossier").created_by
        if not request.user == created_by:
            return Response(
                {"details": "Unauthorized, you are not the owner of the dossier"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ExportedToDocxMixin:
    model = None

    template: str = None
    file_prefix: str = None

    def get(self, request, id, *args, **kwargs):
        try:
            file_name = f"{self.file_prefix}_numero_{id}"
            file_path = self.get_document_path(file_name)
            ctx = self.get_context(request.user, id, *args, **kwargs)
            doc = self.get_document_buffer(ctx, file_path)
            return FileResponse(
                doc,
                as_attachment=True,
                filename=f"{file_name}.docx",
                status=status.HTTP_201_CREATED,
            )
        except ObjectDoesNotExist as e:
            return Response(data={"message": f"{e}"}, status=status.HTTP_404_NOT_FOUND)
        except NotOwner as e:
            return Response(
                data={"message": e.ERROR_MESSAGE}, status=status.HTTP_401_UNAUTHORIZED
            )

    def get_document_buffer(self, ctx, path_to_file: str) -> BufferedWriter:
        doc = DocxTemplate(os.path.abspath(f"{self.template}.docx"))
        doc.render(ctx)
        doc.save(path_to_file)
        return open(path_to_file, "rb")

    def get_context(self, id):
        pass

    def get_document_path(self, file_name: str) -> str:
        pass
