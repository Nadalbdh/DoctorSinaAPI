from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS

from backend.functions import is_municipality_manager

# Open endpoints are the ones that are accessible by anonymous users
OPEN_ENDPOINTS = [
    "CommitteesView",
    "EventsView",
    "EventView",
    "ReportsView",
    "ReportView",
    "NewsView",
    "NewsObjectView",
    "DeprecatedComplaintView",
    "DeprecatedComplaintsView",
    "ComplaintViewSet",
    "DossierView",
    "DossiersView",
    "CommentView",
    "CommentsView",
    "SubjectAccessRequestViewSet",
    "ProcedureView",
    "ProceduresView",
    "StatsView",
    "StatsViewPerDate",
    "GetProfilePictureView",
    "TopicViewSet",
    "ServicesView",
    "AgenciesView",
    "ExportSubjectAccessRequestToDocxView",
    "HealthCheckView",
    "MunicipalityMeta",
    "ManagersView",
    "GetAllAgenciesView",
]


class ReadOnly(BasePermission):
    """
    Only allow requests with the methods 'GET', 'OPTIONS' and 'HEAD'
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class OpenEndpointsAny(BasePermission):
    """
    Only allow access to OPEN_ENDPOINTS, regardless of the method.
    """

    def has_permission(self, request, view):
        return type(view).__name__ in OPEN_ENDPOINTS


class MunicipalityManagerPermission(BasePermission):
    """
    Checks if the user is a manager for the given municipality
    """

    def has_permission(self, request, view):
        request_kwargs = request.resolver_match.kwargs
        if "municipality_id" in request_kwargs:
            return is_municipality_manager(
                request.user, request_kwargs["municipality_id"]
            )
        if "municipality" in request_kwargs:
            return is_municipality_manager(request.user, request_kwargs["municipality"])
        return False


# A safe method and an open endpoint
OpenEndpointsPermission = OpenEndpointsAny & ReadOnly
DefaultPermission = IsAuthenticated | OpenEndpointsPermission

# Only the manager of the corresponding municipality is allowed to modify.
MunicipalityManagerWriteOnlyPermission = (
    DefaultPermission & ReadOnly
) | MunicipalityManagerPermission


class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        request_kwargs = request.resolver_match.kwargs
        if request.method in SAFE_METHODS:
            return True
        if "municipality_id" in request_kwargs:
            return is_municipality_manager(
                request.user, request_kwargs["municipality_id"]
            )

        return False
