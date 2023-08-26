from rest_framework.routers import DefaultRouter, Route


class CustomCRUDRouter(DefaultRouter):
    """
    Only difference from DefaultRouter: use PUT for
    partial_update, and no PATCH
    """

    routes = [
        # List route.
        Route(
            url=r"^{prefix}$",
            mapping={"get": "list", "post": "create"},
            name="{basename}s",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        # Detail route.
        Route(
            url=r"^{prefix}/{lookup}$",
            mapping={
                "get": "retrieve",
                "put": "partial_update",
                "delete": "destroy",
            },
            name="{basename}",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        # Update route.
        Route(
            url=r"^{prefix}/{lookup}/update$",
            mapping={
                "post": "update_status",
            },
            name="{basename}-update",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
    ]
