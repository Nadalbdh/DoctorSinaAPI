from django.db.models import ObjectDoesNotExist
from django.template.loader import render_to_string

from emails.utils import get_sender_email_for, send_mass_html_mail_with_purpose


class BaseEMailService:
    template = None

    def get_subject(self, mobj) -> str:
        raise ValueError("This needs to be implemented")

    def get_mail_object(self):
        """
        Returns *what* is the mail about (this can be a
        single object, a bunch of them, or even a dictionary)
        """
        raise ValueError("This needs to be implemented")

    def get_recipients(self):
        raise ValueError("This needs to be implemented")

    def get_template_params(self, mobj):
        raise ValueError("This needs to be implemented")

    def get_sanitized_subject(self, mobj):
        return self.get_subject(mobj).replace("\n", " ")

    def should_send(self, mobj, recipients):
        return mobj and recipients

    def _render(self, mobj):
        return render_to_string(self.template, self.get_template_params(mobj))

    def send(self):
        raise ValueError("This needs to be implemented")

    def debug(self):
        raise ValueError("This needs to be implemented")


class PerCollectionEMailService(BaseEMailService):
    def send(self):
        objects = self.get_mail_object()
        subject = self.get_sanitized_subject(objects)
        recipients = self.get_recipients()

        if self.should_send(objects, recipients):
            html_message = self._render(objects)
            return send_mass_html_mail_with_purpose(
                [
                    (
                        subject,
                        html_message,
                        get_sender_email_for("notifications"),
                        recipients,
                    )
                ],
                "notifications",
            )
        return 0

    def debug(self):
        print(
            f"""Subject: {self.get_subject(self.get_mail_object())}
Objects: {self.get_mail_object()}
Recipients: {self.get_recipients()}
Sending:
########################################
{self._render(self.get_mail_object())}
########################################
"""
        )


class PerObjectEMailService(BaseEMailService):
    def send(self):
        objects = self.get_mail_object()
        recipients = self.get_recipients()
        emails = []
        for obj in objects:
            subject = self.get_sanitized_subject(obj)
            if self.should_send(obj, recipients):
                html_message = self._render(obj)
                emails.append(
                    (
                        subject,
                        html_message,
                        get_sender_email_for("notifications"),
                        recipients,
                    )
                )
        send_mass_html_mail_with_purpose(emails, "notifications")


class OneObjectEMailService(BaseEMailService):
    def send(self):
        try:
            obj = self.get_mail_object()
        except ObjectDoesNotExist:
            return 0
        recipients = self.get_recipients()
        subject = self.get_sanitized_subject(obj)
        if self.should_send(obj, recipients):
            html_message = self._render(obj)
            return send_mass_html_mail_with_purpose(
                [
                    (
                        subject,
                        html_message,
                        get_sender_email_for("notifications"),
                        recipients,
                    )
                ],
                "notifications",
            )
        return 0
