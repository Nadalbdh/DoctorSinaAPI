import logging

from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags

from backend.helpers import get_managers_by_permission_per_municipality
from backend.models import Municipality
from emails.models import Email
from settings.settings import EMAIL_BCC, EMAIL_CONFIG, EMAIL_HOST_USER

logger = logging.getLogger("default")


def get_managers_emails_by_permission_per_municipality(
    municipality: Municipality, permission
):
    managers = get_managers_by_permission_per_municipality(municipality, permission)
    return [m.user.email for m in managers]


def fetch_all_emails():
    """
    Fetches all emails and groups them per municipality
    """
    emails_per_municipality = (
        Email.objects.all().select_related("municipality").order_by("municipality_id")
    )
    if not emails_per_municipality:
        return []
    grouped_emails = []
    current_emails = []
    current_municipality = emails_per_municipality[0].municipality
    for email_entry in emails_per_municipality:
        if email_entry.municipality_id == current_municipality.pk:
            current_emails.append(email_entry.email)
        else:
            grouped_emails.append(
                {"municipality": current_municipality, "emails": current_emails}
            )
            current_municipality = email_entry.municipality
            current_emails = [email_entry.email]
    grouped_emails.append(
        {"municipality": current_municipality, "emails": current_emails}
    )
    return grouped_emails


# based on https://stackoverflow.com/questions/7583801/send-mass-emails-with-emailmultialternatives/10215091#10215091 and https://github.com/django/django/blob/master/django/core/mail/__init__.py
# TODO maybe refine this and send a PR?
def send_mass_html_mail(
    datatuple, fail_silently=False, auth_user=None, auth_password=None, connection=None
):
    """
    Like send_mass_mail in https://docs.djangoproject.com/en/3.1/topics/email/#send-mass-mail,
    but accepts its content as an html string. The emails are attached with a content without
    html tags, to be used in case html is not supported by the email client.
    """
    connection = connection or get_connection(
        username=auth_user,
        password=auth_password,
        fail_silently=fail_silently,
    )
    messages = [
        generate_email_multi_alternative(
            subject, strip_tags(html_message), sender, recipient, html_message
        )
        for subject, html_message, sender, recipient in datatuple
    ]
    return connection.send_messages(messages)


def generate_email_multi_alternative(
    subject, message, sender, recipients, html_message
):
    mail = EmailMultiAlternatives(subject, message, sender, recipients, bcc=EMAIL_BCC)
    mail.attach_alternative(html_message, "text/html")
    return mail


def get_sender_email_for(purpose: str):
    if purpose in EMAIL_CONFIG and EMAIL_CONFIG[purpose] is not None:
        return EMAIL_CONFIG[purpose]["EMAIL_HOST_USER"]
    return EMAIL_HOST_USER


def get_connection_for(purpose: str, fail_silently=False):
    """
    Returns the connection used for the given purpose
    """
    if purpose not in EMAIL_CONFIG or EMAIL_CONFIG[purpose] is None:
        logger.debug(
            "No valid configuration found for purpose '%s', using default configuration instead",
            purpose,
        )
        return get_connection(fail_silently=fail_silently)

    username = EMAIL_CONFIG[purpose]["EMAIL_HOST_USER"]
    password = EMAIL_CONFIG[purpose]["EMAIL_HOST_PASSWORD"]

    return get_connection(
        username=username, password=password, fail_silently=fail_silently
    )


def send_mass_html_mail_with_purpose(datatuples, purpose, fail_silently=False):
    """
    TODO make this automatically add the sender
    """
    """
    Calls send_mass_html with the connection corresponding to the passed purpose
    """
    connection = get_connection_for(purpose, fail_silently)
    return send_mass_html_mail(datatuples, connection=connection)


def send_html_mail_with_purpose(datatuple, purpose, fail_silently=False):
    """same as send_mass_html_mail_with_purpose but sends one email at a time"""
    return send_mass_html_mail_with_purpose([datatuple], purpose, fail_silently)
