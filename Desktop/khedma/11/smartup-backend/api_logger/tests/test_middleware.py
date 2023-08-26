from django.test import override_settings

from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


def mock_return_input_data(data):
    return data


@override_settings(
    DISABLE_LOGGING_MIDDLEWARE=False, DRF_LOGGER_INTERVAL=0, DRF_LOGGER_QUEUE_MAX_SIZE=1
)
class APILogTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()

    @authenticate_citizen_test
    def test_middleware_log_creation_via_endpoint(self):
        pass

    def test_middleware_log_creation_via_instance_call(self):
        pass
