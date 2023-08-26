from django.urls import include, path

from polls.routers import CustomRouter
from polls.views import ChoicesView, PollsViewSet

polls_router = CustomRouter()
polls_router.register(r"polls", PollsViewSet, basename="poll")

choices_router = CustomRouter()
choices_router.register(r"choices", ChoicesView, basename="choice")

urlpatterns = polls_router.urls + [
    path("polls/<int:poll>/", include(choices_router.urls))
]
