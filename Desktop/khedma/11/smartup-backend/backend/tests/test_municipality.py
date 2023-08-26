import tempfile
from datetime import datetime
from unittest.mock import patch

import absoluteuri
from django.core.files import File
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.text import slugify
from freezegun import freeze_time
from model_bakery import baker
from requests import request
from rest_framework import status

from backend.models import Manager, Municipality
from backend.services.municipality_onboarding import MunicipalityOnBoardingService
from factories import UserFactory
from sms.models import SMSQueueElement

from .test_base import authenticate_manager_test, ElBaladiyaAPITest
from .test_utils import (
    authenticate_citizen,
    check_equal_attributes,
    get_random_municipality_id,
    get_random_municipality_ids,
)


class MunicipalityTest(ElBaladiyaAPITest):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=UserFactory())

    def test_get_all_not_logged_in(self):
        response = self.client.get(
            absoluteuri.build_absolute_uri(reverse("backend:municipalities"))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_all_municipalities(self):
        method = self.client.get
        url = reverse("backend:municipalities")
        response = method(url)
        # Check status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that all municipalities exist
        self.assertTrue(
            all(
                [
                    check_equal_attributes(
                        Municipality.objects.get(pk=m["id"]),
                        m,
                        ["id", "name", "city", "is_active"],  # TODO Check for logo
                    )
                    for m in response.data
                ]
            )
        )
        # Check that all existing municipalities are returned
        self.assertTrue(
            all(
                [
                    m.to_simplified_dict() in response.data
                    for m in Municipality.objects.all()
                ]
            )
        )

    # def test_get_all_municipalities_summary(self):
    #     response = TestRequest(method, url, data).perform()(
    #         self.client.get, reverse("backend:municipalities-summary")
    #     )
    #     # Check status code
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     # Check that all municipalities exist
    #     self.assertTrue(
    #         all(
    #             [
    #                 check_equal_attributes(
    #                     Municipality.objects.get(pk=m["id"]),
    #                     m,
    #                     ["id", "name", "city"],  # TODO Check for logo
    #                 )
    #                 for m in response.data
    #             ]
    #         )
    #     )
    #     # Check that all existing municipalities are returned
    #     self.assertTrue(
    #         all([m.to_simplified_dict() in response.data for m in Municipality.objects.all()])
    #     )

    # def test_get_active_municipalities_summary(self):
    #     response = TestRequest(method, url, data).perform()(
    #         self.client.get, reverse("backend:municipalities-summary"), {"is_active": "True"}
    #     )
    #     # Check status code
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     # Check that all municipalities are active
    #     self.assertTrue(all([m["is_active"] for m in response.data]))
    #     # Check that all municipalities exist
    #     self.assertTrue(
    #         all(
    #             [
    #                 check_equal_attributes(
    #                     Municipality.objects.get(pk=m["id"]),
    #                     m,
    #                     ["id", "name", "city"],  # TODO Check for logo
    #                 )
    #                 for m in response.data
    #             ]
    #         )
    #     )
    #     # Check that all existing municipalities are returned
    #     self.assertTrue(
    #         all([m.to_simplified_dict() in response.data for m in Municipality.objects.filter(is_active=True)])
    #     )

    def test_get_active_municipalities(self):
        for m in Municipality.objects.all():
            m.logo = tempfile.NamedTemporaryFile(suffix=".jpg").name
            m.save()
        # TODO: lots of redundancy between this and test_get_all_municipalities, this should only assert all municipalities are active
        url = reverse("backend:municipalities")
        data = {"is_active": "true"}
        response = self.client.get(url, data)

        # Check status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that all municipalities are active
        self.assertTrue(all([m["is_active"] for m in response.data]))
        # Check that all returned municipalities exist
        self.assertTrue(
            all(
                [
                    check_equal_attributes(
                        Municipality.objects.get(pk=returned_municipality["id"]),
                        returned_municipality,
                        [
                            "id",
                            "name",
                            "name_fr",
                            "city",
                            "is_active",
                            "is_signed",
                            "has_eticket",
                            "longitude",
                            "latitude",
                            "activation_date",
                        ],
                    )
                    for returned_municipality in response.data
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    isinstance(returned_municipality["logo"], str)
                    for returned_municipality in response.data
                ]
            )
        )
        # Check that all existing active municipalities are returned
        self.assertTrue(
            all(
                [
                    db_municipality.to_simplified_dict() in response.data
                    for db_municipality in Municipality.objects.filter(is_active=True)
                ]
            )
        )

    def test_get_not_active_municipalities(self):
        for m in Municipality.objects.all():
            m.logo = tempfile.NamedTemporaryFile(suffix=".jpg").name
            m.save()
        # TODO: lots of redundancy between this and test_get_all_municipalities, this should only assert all municipalities are active
        url = reverse("backend:municipalities")
        data = {"is_active": "false"}
        response = self.client.get(url, data)

        # Check status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that all municipalities are active
        self.assertTrue(all([m["is_active"] == False for m in response.data]))
        # Check that all returned municipalities exist
        self.assertTrue(
            all(
                [
                    check_equal_attributes(
                        Municipality.objects.get(pk=returned_municipality["id"]),
                        returned_municipality,
                        [
                            "id",
                            "name",
                            "name_fr",
                            "city",
                            "is_active",
                            "is_signed",
                            "has_eticket",
                            "longitude",
                            "latitude",
                            "activation_date",
                        ],
                    )
                    for returned_municipality in response.data
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    isinstance(returned_municipality["logo"], str)
                    for returned_municipality in response.data
                ]
            )
        )
        # Check that all existing non active municipalities are returned
        self.assertTrue(
            all(
                [
                    db_municipality.to_simplified_dict() in response.data
                    for db_municipality in Municipality.objects.filter(is_active=False)
                ]
            )
        )

    def test_get_single(self):
        municipality_id = get_random_municipality_id()
        url = reverse("backend:municipality", args=[municipality_id])
        response = self.client.get(url)

        # Check status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the returned object is correct
        self.assertTrue(
            check_equal_attributes(
                Municipality.objects.get(pk=municipality_id),
                response.data,
                ["id", "name", "city", "is_active"],
            )
        )

    def test_get_single_municipality_by_name(self):
        url = reverse(
            "backend:municipality-meta", args=[slugify(self.municipality.name_fr)]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data.keys()),
            sorted(
                [
                    "id",
                    "name",
                    "name_fr",
                    "city",
                    "is_active",
                    "is_signed",
                    "has_eticket",
                    "logo",
                    "longitude",
                    "latitude",
                    "route_name",
                    "activation_date",
                ]
            ),
        )

    def test_get_single_not_logged_in(self):
        municipality_id = get_random_municipality_id()
        response = self.client.get(
            absoluteuri.build_absolute_uri(
                reverse("backend:municipality", args=[municipality_id])
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_single_municipality_by_wrong_name(self):
        url = reverse("backend:municipality-meta", args=["sorry maanech menha hethi"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_single_not_logged_in(self):
        municipality_id = get_random_municipality_id()
        response = self.client.get(
            absoluteuri.build_absolute_uri(
                reverse("backend:municipality", args=[municipality_id])
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate_manager_test
    def test_feature_update(self):
        data = {"service_eticket": "ACTIVATED"}
        self.assertEqual(self.municipality.service_eticket, "DEACTIVATED")
        response = self.client.put(
            reverse("backend:municipality-feature", args=[self.municipality.id]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.municipality.refresh_from_db()
        self.assertEqual(self.municipality.service_eticket, "ACTIVATED")

    @authenticate_manager_test
    @freeze_time("2021-01-12")
    @patch("sms.tasks.flush_pending_sms.delay", return_value=0)
    def test_onboarding_municipality_with_contract_sign_date(self, flush_pending_sms):
        municipality = baker.make("backend.Municipality")
        manager = baker.make("backend.manager", municipality=municipality)
        self.assertIsNone(municipality.contract_signing_date)
        contract_signing_date = datetime.strptime("2021-01-12", "%Y-%m-%d").date()
        MunicipalityOnBoardingService(municipality).sign()
        self.assertEqual(municipality.contract_signing_date, contract_signing_date)
        self.assertEqual(
            municipality.contract_signing_date, manager.user.date_joined.date()
        )

    @authenticate_manager_test
    @freeze_time("2021-01-12")
    @patch("sms.tasks.flush_pending_sms.delay", return_value=0)
    def test_activate_municipality(self, flush_pending_sms):
        municipality = baker.make("backend.Municipality")
        self.assertIsNone(municipality.activation_date)
        date_activation = datetime.strptime("2021-01-12", "%Y-%m-%d").date()
        MunicipalityOnBoardingService(municipality).activate()
        self.assertEqual(municipality.activation_date, date_activation)

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPOGATES=True,
        BROKER_BACKEND="memory",
    )
    @authenticate_manager_test
    @patch("sms.sms_manager.SMSManager.send_sms", return_value=0)
    def test_activate_municipality_(self, send_sms):
        municipality = baker.make("backend.Municipality")
        baker.make(
            "backend.Citizen",
            registration_municipality=municipality,
            _quantity=40,
            user__is_active=True,
        )
        baker.make(
            "backend.Citizen",
            registration_municipality=municipality,
            _quantity=10,
            user__is_active=False,
        )
        self.assertEqual(send_sms.call_count, 0)
        MunicipalityOnBoardingService(municipality).activate()
        self.assertEqual(send_sms.call_count, municipality.registered_citizens.count())

    @authenticate_manager_test
    def test_put_municipality_by_id(self):
        data = {
            "logo": "data:image/png;base64,R0lGODlhAQABAAAAACw=",
            "website": "https://test-url.com/",
            "facebook_url": "https://test-url.com/",
        }
        response = self.client.put(
            reverse("backend:municipality", args=[self.municipality.id]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_municipality_by_id_not_manager(self):
        data = {
            "logo": "data:image/png;base64,R0lGODlhAQABAAAAACw=",
            "website": "https://test-url.com/",
            "facebook_url": "https://test-url.com/",
        }
        response = self.client.patch(
            reverse("backend:municipality", args=[self.municipality.id]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate_manager_test
    def test_delete_municipality_by_id(self):
        response = self.client.delete(
            reverse("backend:municipality", args=[self.municipality.id]),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @authenticate_manager_test
    def test_post_municipality(self):
        data = {
            "id": 1,
            "name": "name ar",
            "name_fr": "name fr",
            "city": "أريانة",
            "is_active": True,
            "is_signed": True,
            "logo": "",
            "latitude": "36.7974230",
            "longitude": "10.1658940",
            "website": None,
            "facebook_url": "https://url_test.com",
            "sms_credit": 500,
            "population": 0,
            "total_sms_consumption": 0,
            "has_eticket": False,
            "activation_date": None,
            "service_eticket": "DEACTIVATED",
            "service_dossiers": "ACTIVATED",
            "service_complaints": "ACTIVATED",
            "service_sar": "ACTIVATED",
            "service_procedures": "ACTIVATED",
            "service_news": "ACTIVATED",
            "service_forum": "ACTIVATED",
            "service_reports": "ACTIVATED",
            "service_events": "ACTIVATED",
            "broadcast_frequency": "7 00:00:00",
            "last_broadcast": None,
        }
        response = self.client.post(
            reverse("backend:municipality", args=[self.municipality.id]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_municipality_by_id_(self):
        response = self.client.get(
            reverse("backend:municipality", args=[self.municipality.id])
        )
        keys = {
            "id",
            "name",
            "name_fr",
            "city",
            "logo",
            "is_active",
            "is_signed",
            "partner_associations",
            "regions",
            "longitude",
            "latitude",
            "website",
            "facebook_url",
            "total_followers",
            "has_eticket",
            "agency",
            "service_eticket",
            "service_dossiers",
            "service_complaints",
            "service_sar",
            "service_procedures",
            "service_news",
            "service_forum",
            "service_reports",
            "service_events",
            "route_name",
            "sms_credit",
            "total_sms_consumption",
            "population",
            "broadcast_frequency",
            "last_broadcast",
            "activation_date",
            "contract_signing_date",
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.keys()), len(keys))


class MunicipalitiesFollowUnfollowTest(ElBaladiyaAPITest):
    def setUp(self):
        self.client.force_authenticate(user=UserFactory())

    def follow_unfollow_routine(
        self, municipality, status_code=status.HTTP_200_OK, follow=True, user=None
    ):
        url = reverse(
            "backend:municipalities-" + ("follow" if follow else "unfollow"),
            args=[municipality],
        )
        if user is None:
            user = authenticate_citizen(self.client)
        response = self.client.post(url)
        # Check correct status code
        self.assertEqual(response.status_code, status_code)
        # return user
        return user

    # Follow
    def test_follow_not_logged_in(self):
        url = absoluteuri.build_absolute_uri(
            reverse("backend:municipalities-follow", args=[1])
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_one(self):
        # Add a citizen
        municipality_id = get_random_municipality_id()
        user = self.follow_unfollow_routine(municipality_id)
        # Check that only one mmunicipality is added
        self.assertEqual(1, user.citizen.municipalities.count())
        # Check that correct municipality is added
        self.assertEqual(
            user.citizen.municipalities.all()[0],
            Municipality.objects.get(pk=municipality_id),
        )

    def test_follow_multiple(self):
        # generate two ids
        [municipality_id_2, municipality_id_1] = get_random_municipality_ids(2)

        # Execute both requests and test status codes
        user = self.follow_unfollow_routine(municipality_id_1)
        self.follow_unfollow_routine(municipality_id_2, user=user)

        municipalities = user.citizen.municipalities
        # Check that both are added
        self.assertEqual(2, municipalities.count())
        # Check that correct municipalities are added
        self.assertTrue(
            Municipality.objects.get(pk=municipality_id_1) in municipalities.all()
        )
        self.assertTrue(
            Municipality.objects.get(pk=municipality_id_2) in municipalities.all()
        )

    def test_follow_same(self):
        # generate id
        municipality_id = get_random_municipality_id()
        user = self.follow_unfollow_routine(municipality_id)
        self.follow_unfollow_routine(municipality_id, user=user)

        municipalities = user.citizen.municipalities
        # Check that one is added
        self.assertEqual(1, municipalities.count())
        # Check that correct municipalities are added
        self.assertTrue(
            Municipality.objects.get(pk=municipality_id) in municipalities.all()
        )

    def test_follow_invalid(self):
        self.follow_unfollow_routine(1000, status.HTTP_404_NOT_FOUND)

    # Unfollow
    def test_unfollow_not_logged_in(self):
        url = absoluteuri.build_absolute_uri(
            reverse("backend:municipalities-unfollow", args=[1])
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unfollow_invalid(self):
        # TODO Expected status code?
        self.follow_unfollow_routine(1, follow=False)

    def test_unfollow_not_existing_municipality(self):
        self.follow_unfollow_routine(1000, status.HTTP_404_NOT_FOUND, follow=False)

    def test_unfollow_valid_single(self):
        # Add a municipality
        user = authenticate_citizen(self.client)
        municipality_id = get_random_municipality_id()
        municipality = Municipality.objects.get(pk=municipality_id)
        user.citizen.municipalities.add(municipality)
        # Remove municipality with endpoint
        self.follow_unfollow_routine(municipality_id, follow=False, user=user)
        self.assertFalse(municipality in user.citizen.municipalities.all())

    def test_unfollow_valid_multiple(self):
        user = authenticate_citizen(self.client)
        [municipality_id_2, municipality_id_1] = get_random_municipality_ids(2)
        municipality1, municipality2 = (
            Municipality.objects.get(pk=municipality_id_1),
            Municipality.objects.get(pk=municipality_id_2),
        )
        user.citizen.municipalities.add(municipality1, municipality2)
        # Remove first municipality
        self.follow_unfollow_routine(municipality_id_1, follow=False, user=user)
        # Check that the behavior is correct
        self.assertFalse(municipality1 in user.citizen.municipalities.all())
        self.assertTrue(municipality2 in user.citizen.municipalities.all())
        # Remove second
        self.follow_unfollow_routine(municipality_id_2, follow=False, user=user)
        self.assertFalse(municipality2 in user.citizen.municipalities.all())
        self.assertEqual(0, user.citizen.municipalities.count())
