from django.urls import path

from emails.views import EMailsView, EMailView, MailingListView

urlpatterns = [
    path(
        "municipalities/<int:municipality_id>/mailing-list", MailingListView.as_view()
    ),
    path("municipalities/<int:municipality_id>/emails/<int:id>", EMailView.as_view()),
    path("municipalities/<int:municipality_id>/emails", EMailsView.as_view()),
]
