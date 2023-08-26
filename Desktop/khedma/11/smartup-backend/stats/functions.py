import datetime
import logging
import math
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from django.db.models import Count, Sum
from django.utils import timezone

from backend.enum import RequestStatus
from backend.models import (
    Association,
    Citizen,
    Comment,
    Complaint,
    Dossier,
    Event,
    Municipality,
    News,
    OperationUpdate,
    Report,
    SubjectAccessRequest,
    UpdatableModel,
)
from etickets_v2.models import Agency, Reservation, Service
from notifications.enums import NotificationActionTypes
from notifications.models import Notification
from settings.settings import METABASE_SITE_URL
from stats.models import EticketsPerformance, OperationUpdatePerformance

CLOSED_STATUSES = [
    RequestStatus.ACCEPTED,
    RequestStatus.REJECTED,
    RequestStatus.NOT_CLEAR,
    RequestStatus.INVALID,
]

logger = logging.getLogger("default")


def get_metabase_url(token):
    return f"{METABASE_SITE_URL}/embed/dashboard/{token.decode('utf-8')}"


def get_global_stats():
    return {
        "active_municipalities": Municipality.objects.filter(is_active=True).count(),
        "signed_municipalities": Municipality.objects.filter(is_signed=True).count(),
        "registered_citizens": Citizen.objects.all().count(),
        "associations": Association.objects.all().count(),
        "nb_of_reservations": Reservation.objects.all().count(),
        "nb_of_complaints": Complaint.objects.all().count(),
        "nb_of_sar": SubjectAccessRequest.objects.all().count(),
        "nb_of_parent_comments": Comment.objects.filter(
            parent_comment__isnull=True
        ).count(),
        "nb_of_dossiers": Dossier.objects.all().count(),
        "nb_of_events": Event.objects.all().count(),
        "nb_of_news": News.objects.all().count(),
        "nb_of_reports": Report.objects.all().count(),
        "operation_updates_totals": OperationUpdate.objects.all().count(),
    }


def get_global_stats_per_date(year=None):
    return {
        "year": year,
        "nb_of_dossiers": Dossier.objects.filter(created_at__year=year).count(),
        "nb_of_complaints": Complaint.objects.filter(created_at__year=year).count(),
        "nb_of_sars": SubjectAccessRequest.objects.filter(
            created_at__year=year
        ).count(),
        "first_municipality_by_followers": Municipality.objects.annotate(
            followers_count=Count("citizens")
        )
        .order_by("-followers_count")
        .values("name", "followers_count")
        .first(),
        "first_municipality_by_news": News.objects.values("municipality__name")
        .annotate(news_count=Count("municipality"))
        .order_by("-news_count")
        .first(),
        "first_municipality_by_complaints": Complaint.objects.filter(
            created_at__year=year
        )
        .values("municipality__name")
        .annotate(complaints_count=Count("municipality"))
        .order_by("-complaints_count")
        .first(),
        "first_municipality_by_sars": SubjectAccessRequest.objects.filter(
            created_at__year=year
        )
        .values("municipality__name")
        .annotate(sars_count=Count("municipality"))
        .order_by("-sars_count")
        .first(),
        "first_municipality_by_dossier": Dossier.objects.filter(created_at__year=year)
        .values("municipality__name")
        .annotate(dossiers_count=Count("municipality"))
        .order_by("-dossiers_count")
        .first(),
    }


def get_officer_kpi_dashboard(municipality_id):
    return {
        "complaints": _status_count(
            Complaint,
            municipality_id=municipality_id,
        ),
        "dossiers": _status_count(
            Dossier,
            municipality_id=municipality_id,
        ),
        "subject_access_requests": _status_count(
            SubjectAccessRequest,
            municipality_id=municipality_id,
        ),
        "forum": _status_count(
            Comment,
            municipality_id=municipality_id,
            parent_comment=None,
        ),
        "events": {
            "upcoming": Event.objects.filter(
                municipality_id=municipality_id, ending_date__gt=datetime.now()
            ).count(),
            "done": Event.objects.filter(
                municipality_id=municipality_id, ending_date__lte=datetime.now()
            ).count(),
        },
        "news": list(
            News.objects.filter(
                municipality_id=municipality_id,
            )
            .values("category")
            .annotate(total=Count("category"))
            .order_by()
        ),
        "reports": list(
            Report.objects.filter(
                municipality_id=municipality_id,
            )
            .values("committee_id")
            .annotate(total=Count("committee"))
            .order_by()
        ),
    }


def _status_count(model, **kwargs):
    """
    count statuses for a subclass model of: UpdatableModel
    """
    statuses = RequestStatus.get_statuses()
    updatable_objects = model.objects.filter(
        municipality_id=kwargs["municipality_id"],
    )
    identifiers = [
        x.operation_updates.all().order_by("-id")[0].id for x in updatable_objects
    ]
    return [
        {
            "status": status,
            "count": model.objects.filter(
                operation_updates__status=status,
                operation_updates__id__in=identifiers,
                **kwargs,
            ).count(),
        }
        for status in statuses
    ]


def _get_instance_timeline_and_status(instance):
    """
    returns a tuple: [(created_at, first_updated_at, first_status ,latest_update_status), ... ] for the instance
    """
    updates = instance.operation_updates.all()
    first_update = None if len(updates) == 1 else updates[1]
    return (
        instance.created_at,
        first_update and first_update.created_at,
        first_update and first_update.status,
        instance.last_operation_update.status,
    )


def _get_timeline_and_status(
    model: UpdatableModel, **kwargs
) -> List[Tuple[date, date, str]]:
    """
    returns a list of tuples [ (created_at, first_updated_at, first_status ,latest_update_status), ... ] for each instance of model
    """
    objects = model.objects.filter(**kwargs)
    return [_get_instance_timeline_and_status(instance) for instance in objects]


def _get_objects_count(updateable_models: List[UpdatableModel], **kwargs):
    return sum(model.objects.filter(**kwargs).count() for model in updateable_models)


def _get_sum_days_difference(items: List[Tuple[date, date, str, str]]) -> Optional[int]:
    """
    returns the sum of days it took to update items
    or None if no operation update has been done
        each item is: [created_at, first_updated_at, first_status ,latest_update_status]
    """
    sum_of_days = 0
    for created_at, first_updated_at, first_status, latest_update_status in items:
        if first_status != None:
            # [:10] to only copy dd-mm-yyyy
            delta = first_updated_at.date() - created_at.date()
            sum_of_days += delta.days
    return sum_of_days


def _calculate_avg_response(
    total_days_taken: int, elements_count: int
) -> Optional[float]:
    if elements_count == None or not total_days_taken:
        # no updatable objects or no operation updates
        return None

    return math.ceil(total_days_taken / elements_count)


def record_operation_performance(
    municipality: Municipality,
    updateable_models: List[UpdatableModel],
    statuses=RequestStatus.get_statuses(),
) -> OperationUpdatePerformance:
    performance = {}
    timelines_per_instance = []
    kwargs = {
        "municipality_id": municipality.id,
        "created_at__gt": datetime.now() - timedelta(days=90),
    }

    for updateable_model in updateable_models:
        timelines_per_instance.extend(
            _get_timeline_and_status(updateable_model, **kwargs)
        )

    # calculate operation type percentages
    objects_count = _get_objects_count(updateable_models, **kwargs)
    operations_statuses = [timeline[3] for timeline in timelines_per_instance]

    for status in statuses:
        count_status = operations_statuses.count(status)
        performance[f"{status.lower()}_percentage"] = get_percentage(
            count_status, objects_count
        )

    percentages_sum = sum(performance.values())
    if int(percentages_sum) != 0 and not (int(percentages_sum) == 100):
        logger.warning(
            f"Operation Update sum doesn't add up for {municipality.name_fr} = {percentages_sum}"
        )

    # calculate response days
    sum_of_days = _get_sum_days_difference(timelines_per_instance)
    performance["average_first_response_days"] = _calculate_avg_response(
        sum_of_days, len(timelines_per_instance)
    )

    operation_update_performance = OperationUpdatePerformance(
        municipality=municipality, **performance
    )
    operation_update_performance.save()
    return operation_update_performance


def get_percentage(of: int, _from: int) -> float:
    return (of / _from) * 100 if _from > 0 else 0


def record_eticket_performance(agency: Agency) -> EticketsPerformance:
    performance = {}
    all_reservations = Service.objects.filter(agency=agency).aggregate(
        Sum("last_booked_ticket")
    )["last_booked_ticket__sum"]
    digital = Reservation.objects.filter(is_physical=False).count()
    physical = Reservation.objects.filter(is_physical=True).count()
    not_digitized = all_reservations - physical - digital

    performance["physical_reservation_percentage"] = get_percentage(
        physical, all_reservations
    )
    performance["digital_reservation_percentage"] = get_percentage(
        digital, all_reservations
    )
    performance["not_digitized_reservation_percentage"] = get_percentage(
        not_digitized, all_reservations
    )
    performance["push_notifications_sent"] = Notification.objects.filter(
        action_type=NotificationActionTypes.ETICKET_RESERVATION
    ).count()

    # TODO log if sum not 100.0
    eticket_performance = EticketsPerformance(agency=agency, **performance)
    eticket_performance.save()
    return eticket_performance


### Exporting KPIs to Excel workbook
def get_count_status(statuses, count_list):
    if isinstance(statuses, str):
        statuses = [statuses]
    count = sum(s['count'] for s in count_list if s['status'] in statuses)
    return count


def get_count_total(count_list):
    total = sum(s['count'] for s in count_list)
    return total


def get_percentage_closed_instances(count_list, closed_statuses=CLOSED_STATUSES):
    total = get_count_total(count_list)
    count = 0
    for s in count_list:
        if s["status"] in closed_statuses:
            count += s['count']
    return get_percentage(count, total)


def get_closed_instance_entire_timeline(model, municipality_id, created_at):
    """
    returns a list of tuples: [(created_at, first_updated_at, last_updated_at, first_update_status, latest_update_status), ... ] for the instance
    """
    objects = model.objects.filter(
        municipality_id=municipality_id, created_at__gt=created_at
    )
    timelines = []
    for instance in objects:
        updates = instance.operation_updates.all()
        first_update = None if len(updates) == 1 else updates[1]
        timelines.append(
            (
                instance.created_at,
                first_update and first_update.created_at,
                instance.last_operation_update.created_at,
                first_update and first_update.status,
                instance.last_operation_update.status,
            )
        )
    return timelines


def get_sum_days_difference_for_closed_operations_final_response(
    items: List[Tuple[date, date, date, str, str]], closed_statuses=CLOSED_STATUSES
) -> Optional[int]:
    """
    returns the sum of days it took to close items
    or None if no operation update has been done
        each item is: (created_at, first_updated_at, last_updated_at, first_update_status, latest_update_status)
    """
    sum_of_days = 0
    for created_at, _, last_updated_at, _, latest_update_status in items:
        if latest_update_status in closed_statuses:
            # [:10] to only copy dd-mm-yyyy
            delta = last_updated_at.date() - created_at.date()
            sum_of_days += delta.days
    return sum_of_days


def get_sum_days_difference_for_first_response(
    items: List[Tuple[date, date, date, str, str]]
) -> Optional[int]:
    """
    returns the sum of days it took to for the first update to be made
    or None if no operation update has been done
        each item is: (created_at, first_updated_at, last_updated_at, first_update_status, latest_update_status)
    """
    sum_of_days = 0
    for created_at, first_updated_at, _, first_update_status, _ in items:
        if first_update_status != None:
            # [:10] to only copy dd-mm-yyyy
            delta = first_updated_at.date() - created_at.date()
            sum_of_days += delta.days
    return sum_of_days


def get_avg_final_response(model, municipality_id, created_at
    ) -> Optional[float]:
    timelines = []
    timelines = get_closed_instance_entire_timeline(model, municipality_id, created_at)
    sum_of_days = get_sum_days_difference_for_closed_operations_final_response(
        timelines
    )
    return _calculate_avg_response(sum_of_days, len(timelines))


def get_avg_first_response(model, municipality_id, created_at
    ) -> Optional[float]:
    timelines = []
    timelines = get_closed_instance_entire_timeline(model, municipality_id, created_at)
    sum_of_days = get_sum_days_difference_for_first_response(timelines)
    return _calculate_avg_response(sum_of_days, len(timelines))


def get_percentage_closed_instances_in_less_than_specific_period(
    model, count_list, municipality_id: int, period, closed_statuses=CLOSED_STATUSES
) -> float:
    kwargs = {
        "municipality_id": municipality_id,
        "last_update__gt": datetime.now() - timedelta(days=period),
    }
    # Filter the complaints based on municipality and within the specified period
    updatable_objects = model.objects.filter(
        municipality_id=municipality_id,
        last_update__gt=datetime.now() - timedelta(days=period),
    )
    number_instances = []
    for status in closed_statuses:
        count = updatable_objects.filter(last_status=status, **kwargs).count()
        number_instances.append({"status": status, "count": count})

    total = get_count_total(count_list)
    count_less_than_period = get_count_total(number_instances)
    return get_percentage(count_less_than_period, total)


def days_since_last_instance(model, municipality_id):
    if model is None:
        return None
    elif model == News:
        last_instance = (
            model.objects.filter(municipality_id=municipality_id)
            .order_by('-published_at')
            .first()
        )
        if last_instance == None:
            return 0
        time_since_last_instance = timezone.now() - last_instance.published_at
    else:
        last_instance = (
            model.objects.filter(municipality_id=municipality_id)
            .order_by('-created_at')
            .first()
        )
        if last_instance == None:
            return 0
        time_since_last_instance = timezone.now() - last_instance.created_at

    return time_since_last_instance.days


def get_digital_tickets_count(municipality_id):
    digital_tickets_count = (
        Service.objects.filter(
            agency__municipality_id=municipality_id, reservations__is_physical=False
        )
        .annotate(num_tickets=Count('reservations'))
        .aggregate(total_tickets=Sum('num_tickets'))['total_tickets']
        or 0
    )

    return digital_tickets_count
