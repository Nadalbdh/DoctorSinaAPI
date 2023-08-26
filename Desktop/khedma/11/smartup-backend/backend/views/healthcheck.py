from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView

from backend.functions import server_works
from etickets_v2.models import Agency


@method_decorator([cache_page(60 * 5)], name="dispatch")
class HealthCheckView(APIView):
    def get(self, request, *args, **kwargs):
        """monitor health of active agencies
        Returns:
            example: [ {"name": "agency 1", "is_up": true}, ... ]
            HTTP_200_OK: all server are running
            HTTP_500_INTERNAL_SERVER_ERROR: atleast 1 server is down
        """
        servers = (
            Agency.objects.filter(is_active=True)
            .order_by("created_at")
            .values_list("name", "local_ip")
        )
        response = [
            {"server_name": s[0], "is_up": server_works(f"{s[1]}/status")}
            for s in servers
        ]
        all_servers_are_up = all([r["is_up"] for r in response])
        status = HTTP_200_OK if all_servers_are_up else HTTP_500_INTERNAL_SERVER_ERROR
        return Response(response, status=status)
