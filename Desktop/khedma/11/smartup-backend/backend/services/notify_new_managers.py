from django.core.mail import EmailMessage
from django.template.loader import get_template

from backend.helpers import get_frontend_url
from backend.models import Municipality
from emails.utils import get_sender_email_for, send_html_mail_with_purpose
from settings.settings import EMAIL_HOST_USER
from utils.SMSManager import SMSManager


class NotifyNewManagerService:
    SMS_TEMPLATES = {
        "first": """تم تكوين الحساب الرقمي ل{} واضافتكم كمتصرف أول باعتماد رقم هاتفكم: {}.
كلمة السر الحالية: {}
 قم بتسجيل الدخول عبر موقع : idara.elbaladiya.tn""",
        "default": """تمت اضافتكم كمتصرف بالحساب الرقمي ل{} باعتماد رقم هاتفكم: {}.
كلمة السر الحالية: {}
 قم بتسجيل الدخول عبر موقع : idara.elbaladiya.tn""",
    }

    def __init__(self, municipality: Municipality, phone_number, email, password):
        self.municipality = municipality
        self.phone_number = phone_number
        self.email = email
        self.password = password

    def notify_first_manager(self):
        self.__notify("first")

    def notify_another_manager(self):
        self.__notify("default")

    def __notify(self, which):
        self.__send_sms_notification(which)
        self.__send_email_notification()

    def __send_sms_notification(self, which):
        sms_content = self.SMS_TEMPLATES[which].format(
            self.municipality.name, self.phone_number, self.password
        )
        SMSManager.send_sms(self.phone_number, sms_content)

    def __send_email_notification(self):
        context = {
            "municipality": self.municipality,
            "pass": self.password,
            "phone": self.phone_number,
        }
        message = get_template("onboarding_email_template.html").render(context)
        subject = (
            " تفعيل المكتب الخلفي لبلدية "
            + self.municipality.name
            + " ولاية "
            + self.municipality.city
            + " للتصرف في البلدية الرقمية "
        )
        datatuple = (
            subject,
            message,
            get_sender_email_for("notifications"),
            [self.email],
        )
        # TODO: remove silent failure
        send_html_mail_with_purpose(
            datatuple, purpose="notifications", fail_silently=True
        )

    def send_activation_email_notification(self):
        url = get_frontend_url(self.municipality)
        context = {
            "municipality": self.municipality,
            "pass": self.password,
            "phone": self.phone_number,
            "url": url,
        }
        message = get_template("onboarding_activation_email_template.html").render(
            context
        )
        subject = (
            " فتح المكتب الخلفي لبلدية "
            + self.municipality.name
            + " ولاية "
            + self.municipality.city
            + " للتصرف في البلدية الرقمية "
        )
        datatuple = (
            subject,
            message,
            get_sender_email_for("notifications"),
            [self.email],
        )
        send_html_mail_with_purpose(
            datatuple, purpose="notifications", fail_silently=True
        )
