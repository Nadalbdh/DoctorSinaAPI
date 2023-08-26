from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from backend.enum import RequestStatus, StatusLabel
from backend.tests.test_base import ElBaladiyaAPITest


class TestStatus(ElBaladiyaAPITest):
    url_name = "backend:status"
    schema_status = [
        RequestStatus.RECEIVED,
        RequestStatus.PROCESSING,
        RequestStatus.ACCEPTED,
        RequestStatus.REJECTED,
        RequestStatus.NOT_CLEAR,
        RequestStatus.INVALID,
    ]
    schema_models = [
        StatusLabel.COMPLAINT,
        StatusLabel.SUBJECT_ACCESS_REQUEST,
        StatusLabel.SUGGESTION,
        StatusLabel.DOSSIER,
        StatusLabel.QUESTION,
        StatusLabel.REMARK,
    ]

    def test_status_labeling(self):
        response = self.client.get(reverse("backend:status"), format="json")
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertCountEqual(
            list(response.data.keys()), ["FRONTOFFICE_LABEL", "BACKOFFICE_LABEL"]
        )

        for key in list(response.data.keys()):
            self.check_models(response.data[key])
            for model in response.data[key].keys():
                self.check_status(response.data[key][model])

    def check_status(self, data):
        self.assertCountEqual(list(data.keys()), self.schema_status)

    def check_models(self, data):
        self.assertCountEqual(list(data.keys()), self.schema_models)
