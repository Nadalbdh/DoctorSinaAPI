from .account_management_views import *
from .association_views import *
from .crud_views import *
from .manager_views import *
from .municipality_views import *
from .news_tag_views import *
from .sms_broadcast_views import *
from .static_text_views import *

"""
    Code Status Manual:
        status.HTTP_200_OK : Success (Get, PUT, Delete)
        status.HTTP_201_CREATED : Success  (POST)
        status.HTTP_500_INTERNAL_SERVER_ERROR : Runtime Error (Server Error)
        status.HTTP_400_BAD_REQUEST : Wrong request format (Missed required parameter ...)
        status.HTTP_401_UNAUTHORIZED : No Such Token (The Token does not belong to any request)
"""
