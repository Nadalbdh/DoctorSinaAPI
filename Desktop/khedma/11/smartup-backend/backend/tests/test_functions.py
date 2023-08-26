import unittest
from subprocess import CalledProcessError
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase

from backend.functions import convert_base64_to_image, server_works
from backend.serializers.default_serializer import validator_string_is_base_64_img


class FunctionsViewTest(unittest.TestCase):
    @patch("subprocess.run")
    def test_server_works_success(self, mock_run):
        mock_run.return_value.returncode = 0
        adrss = "example.com"
        result = server_works(adrss + "/status")
        mock_run.assert_called_with(
            f"curl --connect-timeout 2 --max-time 2 --fail {adrss}/status",
            shell=True,
            check=True,
            timeout=2,
        )
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_server_works_failure(self, mock_run):
        mock_run.return_value.returncode = 1
        adrss = "example.com"
        result = server_works(adrss + "/status")
        mock_run.assert_called_with(
            f"curl --connect-timeout 2 --max-time 2 --fail {adrss}/status",
            shell=True,
            check=True,
            timeout=2,
        )
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_server_works_exception(self, mock_run):
        mock_run.side_effect = CalledProcessError(1, "ping -c wewe -W messed it up")
        adrss = "website.tn.com"
        result = server_works(adrss)
        self.assertFalse(result)


class Base64ImageTest(TestCase):
    def test_validator_string_is_base_64_img(self):
        valid_base64_strings = [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADaQHpI+3uEwAAAABJRU5ErkJggg==",
            "data:image/gif;base64,R0lGODlhAQABAAAAACw=",
            "data:image/jpeg;base64,R0lGODlhAQABAAAAACw=",
        ]
        for valid_base64_string in valid_base64_strings:
            self.assertIsNone(validator_string_is_base_64_img(valid_base64_string))

        invalid_base64_string = "invalid_base64_string"
        with self.assertRaises(Exception):
            validator_string_is_base_64_img(invalid_base64_string)

        invalid_image_type = "data:text/plain;base64,SGVsbG8="
        with self.assertRaises(Exception):
            validator_string_is_base_64_img(invalid_image_type)

        invalid_image_data = "data:image/png;base64,invalid_image_data"
        with self.assertRaises(Exception):
            validator_string_is_base_64_img(invalid_image_data)

    @patch("uuid.uuid4")
    def test_convert_base64_to_image(self, mock_uuid):
        mock_uuid.return_value.hex = "abcd1234"
        valid_base64_string = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADaQHpI+3uEwAAAABJRU5ErkJggg=="
        expected_file_name = "abcd1234.png"
        expected_content_file = ContentFile(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9c\xec\xbd\x07\x00\x02\xb1\x01\xb5\x02\x00\x00\x00\x00IEND\xaeB`\x82",
            name=expected_file_name,
        )
        content_file = convert_base64_to_image(valid_base64_string, "test.png")
        print(expected_content_file.read())
        print(content_file.read())
        self.assertEqual(expected_content_file.read(), content_file.read())

        invalid_base64_string = "invalid_base64_string"
        with self.assertRaises(Exception) as context:
            convert_base64_to_image(invalid_base64_string, "test.png")
