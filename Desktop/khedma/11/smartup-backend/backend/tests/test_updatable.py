from parameterized import parameterized

from backend.enum import RequestStatus
from backend.models import Complaint, Dossier, Municipality, SubjectAccessRequest
from backend.tests.baker import add_status, bake_updatable
from backend.tests.test_base import TestBase
from backend.tests.test_utils import get_random_municipality_id

# The models that are included in the overview (model, related_name)
updatable_models = [
    ("complaint", Complaint),
    ("subjectaccessrequest", SubjectAccessRequest),
    ("dossier", Dossier),
]


class TestUpdatableModel(TestBase):
    def setUp(self):
        self.municipality = Municipality.objects.get(pk=get_random_municipality_id())

    @parameterized.expand(updatable_models)
    def test_last_update_manager_all_there(self, model_name, model_class):
        obj1 = bake_updatable(
            "backend." + model_name,
            "2020-10-10",
            RequestStatus.ACCEPTED,
            "2021-05-30",
            self.municipality,
        )
        add_status(obj1, RequestStatus.REJECTED, "2021-05-31")

        obj2 = bake_updatable(
            "backend." + model_name,
            "2019-03-10",
            RequestStatus.PROCESSING,
            "2019-05-30",
            self.municipality,
        )

        obj3 = bake_updatable(
            "backend." + model_name,
            "2019-03-10",
            RequestStatus.PROCESSING,
            "2019-05-30",
            self.municipality,
        )
        objs = model_class.objects.all()

        self.assertCountEqual(objs, [obj1, obj2, obj3])

    @parameterized.expand(updatable_models)
    def test_last_update_manager_annotated(self, model_name, model_class):
        obj = bake_updatable(
            "backend." + model_name,
            "2019-03-10",
            RequestStatus.PROCESSING,
            "2019-05-30",
            self.municipality,
        )
        add_status(obj, RequestStatus.ACCEPTED, "2020-01-02")
        add_status(obj, RequestStatus.REJECTED, "2021-12-03")  # Last
        add_status(obj, RequestStatus.PROCESSING, "2020-03-03")
        add_status(obj, RequestStatus.ACCEPTED, "2020-05-30")

        actual = model_class.objects.last()

        # The annotated values are correct
        self.assertDateRepr(actual.last_update, "2021-12-03")
        self.assertEqual(actual.last_status, RequestStatus.REJECTED)

    @parameterized.expand(updatable_models)
    def test_last_update_manager_order(self, model_name, model_class):
        # The more recent
        obj1 = bake_updatable(
            "backend." + model_name,
            "2020-07-23",
            RequestStatus.REJECTED,
            "2021-01-03",
            self.municipality,
        )
        add_status(obj1, RequestStatus.ACCEPTED, "2020-09-30")

        # The older
        obj2 = bake_updatable(
            "backend." + model_name,
            "2020-08-15",
            RequestStatus.REJECTED,
            "2020-09-10",
            self.municipality,
        )

        actual = model_class.objects.all()
        self.assertEqual(actual[0], obj1)
        self.assertEqual(actual[1], obj2)
