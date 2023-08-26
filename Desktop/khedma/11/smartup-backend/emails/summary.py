from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.timezone import now, timedelta

from backend.enum import RequestStatus
from backend.models import Comment, Complaint, Municipality, SubjectAccessRequest


class Summary:
    """Represents a summary for a given timespan
    :param start_date: start date of the summary
    :type start_date: date
    :param end_date: end date of the summary
    :type end_date: date
    """

    def __init__(self, previous_date, municipality_id):
        self.previous_date = previous_date
        self.municipality_id = municipality_id
        self.municipality = Municipality.objects.get(pk=municipality_id)
        # more convenient
        self._content_types = ContentType.objects.get_for_models(
            Complaint, SubjectAccessRequest
        )

    def get_full_summary(self):
        return {
            "citizens": self.get_citizens_summary(),
            "committees": self.get_committees_summary(),
            "dossiers": self.get_dossiers_summary(),
            "complaints": self.get_complaints_summary(),
            "subject_access_requests": self.get_subject_access_requests_summary(),
            "news": self.get_news_summary(),
        }

    ###########################################################################
    #                             General Helpers                             #
    ###########################################################################

    def get_total_and_delta_from_queryset(self, queryset, condition):
        """
        Given a queryset and how to calculate the previous state, returns a
        dictionary with the total count and the difference
        """
        total = queryset.count()
        previous = queryset.filter(condition).count()
        return {
            "total": total,
            "delta": total - previous,
        }

    ###########################################################################
    #                                 Citizens                                #
    ###########################################################################

    def get_starred_citizens(self):
        return self.municipality.total_starred()

    def get_registered_citizens(self):
        queryset = self.municipality.registered_citizens.all()
        condition = Q(user__date_joined__lt=self.previous_date)
        return self.get_total_and_delta_from_queryset(queryset, condition)

    def get_followed_citizens(self):
        return self.municipality.total_followed()

    def get_citizens_summary(self):
        return {
            "registered": self.get_registered_citizens(),
            "starred": self.get_starred_citizens(),
            "followed": self.get_followed_citizens(),
        }

    ###########################################################################
    #                                 Dossiers                                #
    ###########################################################################

    def get_dossiers_summary(self):
        queryset = self.municipality.dossiers.all()
        condition = Q(created_at__lt=self.previous_date)
        return self.get_total_and_delta_from_queryset(queryset, condition)

    ###########################################################################
    #                                   News                                  #
    ###########################################################################
    def get_news_summary(self):
        queryset = self.municipality.news.all()
        condition = Q(published_at__lt=self.previous_date)
        return self.get_total_and_delta_from_queryset(queryset, condition)

    ###########################################################################
    #                                Committees                               #
    ###########################################################################

    def get_reports_summary(self):
        queryset = self.municipality.reports.all()
        condition = Q(date__lt=self.previous_date)
        return self.get_total_and_delta_from_queryset(queryset, condition)

    def get_posts_summary(self):
        queryset = Comment.posts.filter(municipality=self.municipality)
        condition = Q(created_at__lt=self.previous_date)
        return self.get_total_and_delta_from_queryset(queryset, condition)

    def get_comments_summary(self):
        queryset = Comment.comments.filter(municipality=self.municipality)
        condition = Q(created_at__lt=self.previous_date)
        return self.get_total_and_delta_from_queryset(queryset, condition)

    def get_forum_summary(self):
        return {
            "comments": self.get_comments_summary(),
            "posts": self.get_posts_summary(),
        }

    def get_committees_summary(self):
        return {
            "reports": self.get_reports_summary(),
            "forum": self.get_forum_summary(),
        }

    ###########################################################################
    #                                Complaints                               #
    ###########################################################################

    def get_complaints_summary(self):
        return self._get_updatable_objects_summary(
            self.municipality.complaints, Complaint
        )

    ###########################################################################
    #                         Subject Access Requests                         #
    ###########################################################################

    def get_subject_access_requests_summary(self):
        return self._get_updatable_objects_summary(
            self.municipality.subject_access_requests, SubjectAccessRequest
        )

    ###########################################################################
    #                        Updatable Objects Helpers                        #
    ###########################################################################

    def _get_all_updatable_objects(self, queryset):
        return self.get_total_and_delta_from_queryset(
            queryset, Q(created_at__lt=self.previous_date)
        )

    def _get_updatable_objects_summary(self, queryset, model):
        result = {
            status.lower(): self._get_status_updatable_objects(model, status)
            for status in RequestStatus.get_statuses()
        }

        result["all"] = self._get_all_updatable_objects(queryset)
        result["urgent"] = self._get_urgent_updatable_objects(model)
        return result

    def _get_status_updatable_objects(self, model, status):
        return model.objects.filter(
            last_status=status, municipality=self.municipality
        ).count()

    def _get_urgent_updatable_objects(self, model):
        return model.objects.filter(
            municipality=self.municipality,
            last_status__in=[RequestStatus.RECEIVED, RequestStatus.PROCESSING],
            created_at__lt=now() - timedelta(days=21),
        ).count()
