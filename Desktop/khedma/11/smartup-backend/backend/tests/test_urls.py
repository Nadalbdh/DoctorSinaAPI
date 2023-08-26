from django.urls import resolve, Resolver404
from parameterized import parameterized

from backend.tests.test_base import TestBase

urls = [
    ("municipality", "/api/municipalities/1"),
    # Complaints
    ("complaints", "/api/municipalities/4/complaints"),
    ("complaint", "/api/municipalities/3/complaints/412"),
    ("complaint-update", "/api/municipalities/6/complaints/23/update"),
]


class URLResolverTest(TestBase):
    @parameterized.expand(urls)
    def test_valid_url(self, url_name, path):
        try:
            match = resolve(path)
            self.assertEqual(match.url_name, url_name)
        except Resolver404:
            self.fail(f"Path {path} could not be resolved")
