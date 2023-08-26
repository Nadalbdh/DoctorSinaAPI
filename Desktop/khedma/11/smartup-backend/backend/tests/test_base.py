import shutil

from django.db.models import FileField
from django.test import override_settings, TestCase
from django.urls import reverse
from faker import Faker
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from backend import models
from backend.tests.test_utils import get_random_municipality_id


class CustomAssertionsTestMixin:
    """
    A mixin that adds custom assertions for test classes
    """

    def assertDateRepr(self, actual, expected: str, date_format: str = "%Y-%m-%d"):
        self.assertEqual(actual.strftime(date_format), expected)

    def assertFileIsNone(self, actual):
        self.assertFalse(bool(actual), f"{actual} is not None")

    def assertFileIsNotNone(self, actual):
        self.assertTrue(bool(actual), f"{actual} is None")

    def assertFileExists(self, actual: FileField):
        self.assertTrue(actual.storage.exists(actual.name))

    def assertFileNotExists(self, actual: FileField):
        self.assertFalse(actual.storage.exists(actual.name))

    def assertEmpty(self, actual):
        self.assertFalse(actual, f"{actual} is not empty")

    def assertNotFoundResponse(self, actual, should_have_details: bool = True):
        self.assertEqual(actual.status_code, status.HTTP_404_NOT_FOUND)
        if should_have_details:
            self.assertEqual(actual.data, {"detail": "Not found."})

    def assertForbiddenResponse(self, actual, content=None):
        if content is None:
            content = {"detail": "You do not have permission to perform this action."}
        self.assertEqual(actual.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(actual.data, content)


class MunicipalityTestMixin:
    """
    This mixin loads the municipalities fixture, and sets a random municipality.
    """

    fixtures = ["municipalities"]

    default_model: str = None

    def setUp(self):
        super().setUp()
        self.municipality = models.Municipality.objects.get(
            pk=get_random_municipality_id()
        )

    def make_with_municipality(self, model: str = None, *args, **kwargs):
        if self.default_model is not None and model is None:
            return baker.make(
                self.default_model, *args, **kwargs, municipality=self.municipality
            )
        if model is not None:
            return baker.make(model, *args, **kwargs, municipality=self.municipality)
        return baker.make(*args, **kwargs, municipality=self.municipality)

    def other_municipality(self):
        pk = get_random_municipality_id()
        while self.municipality.pk == pk:
            pk = get_random_municipality_id()
        return models.Municipality.objects.get(pk=pk)


class TestBase(TestCase, CustomAssertionsTestMixin):  # TODO do we need this?
    fixtures = ["municipalities"]
    fake = Faker()


class URLTestMixin:
    """
    This mixins provides some shortcuts to retrieve the URLs.
    """

    url_name = None
    url_name_plural = None

    def get_url_name(self) -> str:
        assert self.url_name is not None, "Define url_name or override this method"
        return self.url_name

    def get_url_name_plural(self) -> str:
        if self.url_name_plural is not None:
            return self.url_name_plural
        url_name = self.get_url_name()
        return url_name + "s"

    def get_url(self, pk: int = None, url_name: str = None):
        args = [self.municipality.pk]

        if pk is not None:
            args.append(pk)

        if url_name is None:
            url_name = (
                self.get_url_name() if pk is not None else self.get_url_name_plural()
            )

        return reverse(url_name, args=args)


class ElBaladiyaAPITest(
    MunicipalityTestMixin,
    CustomAssertionsTestMixin,
    URLTestMixin,
    APITestCase,
):
    def setUp(self):
        super().setUp()
        self.citizen = baker.make("backend.citizen")
        self.manager = baker.make("backend.manager", municipality=self.municipality)


def cleanup_test_files(method):
    """
    A decorater to remove files created during a test
    """
    TEST_DIR = "test_dir"

    @override_settings(MEDIA_ROOT=(TEST_DIR + "/media"))
    def decorated(ref, *args, **kwargs):
        method(ref, *args, **kwargs)
        try:
            shutil.rmtree(TEST_DIR)
        except OSError:
            pass

    return decorated


def authenticate_citizen_test(method):
    """
    A decorater to be used with ElBaladiyaAPITest tests that bypass authentication.
    """

    def decorated(ref, *args, **kwargs):
        ref.client.force_authenticate(user=ref.citizen.user)
        method(ref, *args, **kwargs)

    return decorated


def authenticate_manager_test(method):
    """
    A decorater to be used with ElBaladiyaAPITest tests that bypass authentication.
    """

    def decorated(ref, *args, **kwargs):
        ref.client.force_authenticate(user=ref.manager.user)
        method(ref, *args, **kwargs)

    return decorated
