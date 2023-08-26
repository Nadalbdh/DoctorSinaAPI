from datetime import datetime

from django.shortcuts import get_object_or_404
from pytz import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from backend.decorators import IsValidGenericApi, ReplaceKwargs
from backend.mixins import ElBaladiyaModelViewSet, SetCreatedByMixin
from polls.mixins import PollPermissionViewSetMixin
from polls.models import Choice, ChoiceType, Poll
from polls.serializers import ChoiceSerializer, PollSerializer
from settings.custom_permissions import (
    DefaultPermission,
    MunicipalityManagerWriteOnlyPermission,
    ReadOnly,
)


@IsValidGenericApi()
class PollsViewSet(
    SetCreatedByMixin, PollPermissionViewSetMixin, ElBaladiyaModelViewSet
):
    serializer_class = PollSerializer
    model = Poll
    permission_classes = [
        MunicipalityManagerWriteOnlyPermission | ReadOnly,
    ]

    @action(
        detail=True,
        methods=["post"],
        url_path="vote",
        url_name="vote",
        permission_classes=[DefaultPermission],
    )
    def multi_vote(self, request, municipality, pk):
        selected_choices_list = request.query_params.getlist("choices")
        poll = get_object_or_404(Poll, pk=pk)
        if poll.kind != ChoiceType.SINGLE_CHOICE.value and selected_choices_list:
            now_tunis = datetime.now(timezone("Africa/Tunis"))
            # Vote can be made only between start & end
            if now_tunis > poll.ends_at or now_tunis < poll.starts_at:
                raise ValidationError({"message": "Poll is not available now !"})
            try:
                selected_choices_list = list(map(int, selected_choices_list))
            except ValueError:
                raise ValidationError({"message": "Choices invalid"})
            selected_choices = Choice.objects.filter(
                poll=poll, pk__in=selected_choices_list
            )
            if not selected_choices:
                raise ValidationError({"message": "Choices invalid"})
            for c in poll.choices.all():
                c.voters.remove(request.user)
            for c in selected_choices:
                c.voters.add(request.user)
            return Response(data={"message": "Your vote has been submitted !"})
        raise ValidationError({"message": "Poll is single choice"})


@ReplaceKwargs({"municipality": "poll__municipality_id"})
@IsValidGenericApi()
class ChoicesView(PollPermissionViewSetMixin, ElBaladiyaModelViewSet):
    model = Choice
    serializer_class = ChoiceSerializer
    permission_classes = [
        MunicipalityManagerWriteOnlyPermission | ReadOnly,
    ]

    @action(
        detail=True,
        methods=["post"],
        url_path="vote",
        url_name="vote",
        permission_classes=[DefaultPermission],
    )
    def single_vote(self, request, poll__municipality_id, poll, pk):
        poll = get_object_or_404(Poll, pk=poll)
        if poll.kind == ChoiceType.SINGLE_CHOICE.value:
            now_tunis = datetime.now(timezone("Africa/Tunis"))
            # Vote can be made only between start & end
            if now_tunis > poll.ends_at or now_tunis < poll.starts_at:
                raise ValidationError({"message": "Poll is not available now !"})
            choice = get_object_or_404(self.model, pk=pk)
            if poll.kind == ChoiceType.SINGLE_CHOICE.value:
                for c in poll.choices.all():
                    c.voters.remove(request.user)
            choice.voters.add(request.user)
            return Response(data={"message": "Your vote has been submitted !"})
        raise ValidationError({"message": "Poll is multi choice"})
