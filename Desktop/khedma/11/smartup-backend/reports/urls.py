from django.urls import path

from reports.views import PDFComplaintReport, PDFSubjectAccessReport

app_name = "reports"

urlpatterns = (
    path(
        "municipalities/<int:municipality_id>/complaints-report/",
        PDFComplaintReport.as_view(),
        name="complaints",
    ),
    path(
        "municipalities/<int:municipality_id>/subject-access-requests-report/",
        PDFSubjectAccessReport.as_view(),
        name="sars",
    ),
)
