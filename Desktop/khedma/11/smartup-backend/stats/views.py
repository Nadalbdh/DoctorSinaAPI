import time

import jwt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from backend.decorators import IsValidGenericApi
from settings.custom_permissions import MunicipalityManagerWriteOnlyPermission
from settings.settings import METABASE_SECRET_KEY
from stats.functions import (
    get_global_stats,
    get_global_stats_per_date,
    get_metabase_url,
    get_officer_kpi_dashboard,
)
from stats.serializer import SignMetabaseEmbedSerializer

CACHE_FOR = 60 * 5  # 5 minutes


@IsValidGenericApi()
@method_decorator([cache_page(CACHE_FOR)], name="dispatch")
class StatsView(GenericAPIView):
    """Baladiya.tn stats"""

    def get(self, request):
        return JsonResponse(data=get_global_stats())


@IsValidGenericApi()
@method_decorator([cache_page(CACHE_FOR)], name="dispatch")
class StatsViewPerDate(GenericAPIView):
    """Baladiya.tn stats per date"""

    def get(self, request, year):
        return JsonResponse(data=get_global_stats_per_date(year=year))


@IsValidGenericApi()
@method_decorator([cache_page(CACHE_FOR)], name="dispatch")
class KPIView(GenericAPIView):
    """KPIs for officers dashboard UI"""

    permission_classes = [MunicipalityManagerWriteOnlyPermission]

    def get(self, request, municipality_id):
        data = get_officer_kpi_dashboard(municipality_id)
        return JsonResponse(data=data)


@IsValidGenericApi()
class SignMetabaseEmbed(GenericAPIView):
    """KPIs for officers metabase embed"""

    serializer_class = SignMetabaseEmbedSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, serializer, **kargs):
        payload = {
            "resource": {"dashboard": kargs["dashboard_id"]},
            "params": {**request.data},
            "exp": round(time.time()) + (60 * 10),  # 10 minute expiration
        }
        token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
        return JsonResponse(data={"link": get_metabase_url(token)})
