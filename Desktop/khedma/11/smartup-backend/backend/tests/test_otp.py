from random import randint
from unittest.mock import patch

from django.core.cache import cache
from model_bakery import baker

from backend.enum import CachePrefixes
from backend.registration_otp_manager import (
    add_otp,
    check_registration_otp,
    MAX_OTP_RETRIES,
    prepare_registration_otp,
)
from backend.tests.test_base import TestBase
from backend.tests.test_utils import get_random_phone_number
from sms.enum import SMSQueueStatus


class OTPTest(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    ###########################################################################
    #                             Helper Functions                            #
    ###########################################################################

    @staticmethod
    def get_otps(phone_number):
        return cache.get("{}:{}".format(CachePrefixes.REGISTER, phone_number))

    @staticmethod
    def set_otps(phone_number, otps):
        cache.set("{}:{}".format(CachePrefixes.REGISTER, phone_number), otps, 7200)

    @staticmethod
    def get_random_otp():
        # TODO use a phone number random generator
        return str(randint(900000, 999999))

    ###########################################################################
    #                                  Tests                                  #
    ###########################################################################

    def setUp(self):
        # Generate new values for each run
        self.phone_number = get_random_phone_number()
        self.otps = [OTPTest.get_random_otp() for _ in range(MAX_OTP_RETRIES)]
        self.otp = self.fake.random_element(self.otps)

    # add_otp
    def test_add_otp(self):
        return_value = add_otp(self.phone_number, self.otp)
        self.assertTrue(return_value)

        cached_otps = OTPTest.get_otps(self.phone_number)
        self.assertIn(self.otp, cached_otps)

    def test_add_otp_multiple(self):
        # Add the otps
        for otp in self.otps:
            returned_value = add_otp(self.phone_number, otp)
            self.assertTrue(returned_value)

        cached_otps = OTPTest.get_otps(self.phone_number)
        self.assertCountEqual(cached_otps, self.otps)

    def test_add_otp_above_threshhold(self):
        OTPTest.set_otps(self.phone_number, self.otps)
        returned_value = add_otp(self.phone_number, OTPTest.get_random_otp())
        self.assertFalse(returned_value)

    # check otp
    def test_check_otp_empty(self):
        OTPTest.set_otps(self.phone_number, [])
        self.assertFalse(check_registration_otp(self.phone_number, self.otp))

    def test_check_otp_valid_one(self):
        OTPTest.set_otps(self.phone_number, [self.otp])
        self.assertTrue(check_registration_otp(self.phone_number, self.otp))

    def test_check_otp_valid_multiple(self):
        OTPTest.set_otps(self.phone_number, self.otps)
        self.assertTrue(check_registration_otp(self.phone_number, self.otp))

    # prepare_registration
    # we patch this *inside* the test, because we still want it to be random (no hardcoding)
    @patch("backend.registration_otp_manager.randint")
    @patch("backend.registration_otp_manager.add_otp", return_value=True)
    @patch("utils.SMSManager.SMSManager.send_sms", return_value=0)
    def test_prepare_registration_otp_correct(
        self, sms_mock, add_otp_mock, randint_mock
    ):
        # patching
        randint_mock.return_value = self.otp

        # TODO use recipes
        citizen = baker.make("backend.citizen", user__username=self.phone_number)
        user = citizen.user

        result = prepare_registration_otp(user)

        # We called add_otp with the correct otp, exactly once
        add_otp_mock.assert_called_once()
        add_otp_mock.assert_called_with(user.get_username(), self.otp)

        # We attempted to send only one correct sms
        template_sms = "{} est le code de confirmation de votre compte elBaladiya.tn."
        sms_mock.assert_called_once()
        sms_mock.assert_called_with(user.get_username(), template_sms.format(self.otp))

        # We return success
        self.assertEqual(result, 0)

    @patch("backend.registration_otp_manager.add_otp", return_value=False)
    @patch("utils.SMSManager.SMSManager.send_sms")
    def test_prepare_registration_otp_threshold(self, sms_mock, add_otp_mock):
        # TODO use recipes
        citizen = baker.make("backend.citizen", user__username=self.phone_number)
        user = citizen.user

        result = prepare_registration_otp(user)

        # We called add_otp with the correct otp, exactly once
        add_otp_mock.assert_called_once()

        # We did not send anything
        sms_mock.assert_not_called()

        # We return success
        self.assertEqual(result, SMSQueueStatus.TOO_MANY_ATTEMPTS)

    # TODO add tests for the other SMSManager return values after refactoring that class
