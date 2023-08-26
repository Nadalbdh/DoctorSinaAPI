import logging
from functools import wraps

from rest_framework.serializers import Serializer

from backend.functions import is_municipality_manager
from settings.settings import FRONTEND_URL

logger = logging.getLogger("default")


def prefix_citizen_url(prop):
    def _decorated(self):
        suffix = prop(self)
        return f"{FRONTEND_URL}/{self.municipality.get_route_name()}/{suffix}".replace(
            " ", "-"
        )

    return _decorated


class IsValidGenericApi:
    def __init__(self, post=True, put=True, get=False):
        # By default, all post and put requests are decorated
        self.get = get
        self.post = post
        self.put = put

    def __call__(self, klass):
        if self.get:
            self.decorate_method(klass, "get")
        if self.post:
            self.decorate_method(klass, "post")
        if self.put:
            self.decorate_method(klass, "put")
        return klass

    def decorate_method(self, klass, method):
        if not hasattr(klass, method):
            return
        old_method = getattr(klass, method)

        @wraps(getattr(klass, method))
        def decorated_method(self, request, **kwargs):
            data = dict()
            if request.method == "POST":
                data = request.data.copy()
            if request.method == "GET":
                data = request.GET.copy()
            if request.method == "PUT":
                data = request.data.copy()
            data.update(kwargs)
            serializer: Serializer = self.serializer_class(data=data)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as errors:
                logger.warning("%s %s %s", request.method, request.path, errors)
                raise errors
            return old_method(self, request, serializer, **kwargs)

        setattr(klass, method, decorated_method)
        return klass


class ReplaceKwargs:
    """
    A decorator to update the kwargs before calling get_queryset
    """

    def __init__(self, url_mappings):
        self.url_mappaings = url_mappings

    def __call__(self, klass):
        old_getqueryset = getattr(klass, "get_queryset")
        url_mappings = self.url_mappaings

        @wraps(getattr(klass, "get_queryset"))
        def decorated_getqueryset(self):
            # The state shouldn't be visibly changed
            old_kwargs = self.kwargs.copy()
            # Replace the specified kwargs
            for to_replace in url_mappings:
                if to_replace in self.kwargs:
                    self.kwargs[url_mappings[to_replace]] = self.kwargs[to_replace]
                    self.kwargs.pop(to_replace)
            queryset = old_getqueryset(self)
            # Return the kwargs like they were
            self.kwargs = old_kwargs
            return queryset

        setattr(klass, "get_queryset", decorated_getqueryset)
        return klass


def request_user_field(default=None):
    """
    A decorator to make `get_FIELD` methods in serializers
    take an additional `user` argument.
    In case the request cannot be accessed, the default
    paramater is returned.
    """

    def decorator(method):
        def wrapper(self, obj):
            if "request" in self.context:
                user = self.context["request"].user
                return method(self, obj, user)
            return default

        return wrapper

    return decorator


def only_managers(default=None):
    """
    A decorator to make `get_FIELD` methods to make the
    underlying field only viewable when the user of the
    request is a manager.

    TODO this is generalizable (e.g. taking an arbitrary
    predicate instead)
    """

    def decorator(method):
        @request_user_field(default=default)
        def wrapper(self, obj, user):
            if is_municipality_manager(user=user, municipality_id=obj.municipality.id):
                return method(self, obj)
            return default

        return wrapper

    return decorator
