from django.template.loader import render_to_string
from django.utils import timezone

from emails.summary import Summary
from emails.utils import (
    fetch_all_emails,
    get_sender_email_for,
    send_mass_html_mail_with_purpose,
)

SUBJECT_TEMPLATE = "الإحصائيات الخاصة بحساب {municipality_name} بتاريخ {date}"
SENDER = get_sender_email_for("statistics")

date_format = "%d/%m/%Y"


class WeeklyEMailService:
    @staticmethod
    def send_weekly_email():
        """
        Send the weekly summary
        """
        # [{"municipality_id": id, "emails":[email@test.com, ..]}, ...]
        emails_per_municipality = fetch_all_emails()
        # (Subject, Content, From, Recipient list)
        emails = [
            WeeklyEMailService.__generate_mail_tuple(municipality_emails)
            for municipality_emails in emails_per_municipality
        ]
        send_mass_html_mail_with_purpose(emails, "statistics")

        ###########################################################################
        #                                 Helpers                                 #
        ###########################################################################

    @staticmethod
    def __render_html_content(municipality, number_emails):
        today_date = timezone.now()
        last_week_date = timezone.now() - timezone.timedelta(days=7)
        summary = Summary(last_week_date, municipality.pk).get_full_summary()
        return render_to_string(
            "email_template.html",
            {
                "municipality_name": municipality.name,
                "today": today_date,
                "number_emails": number_emails,
                "summary": summary,
            },
        )

    @staticmethod
    def __generate_mail_tuple(municipality_emails):
        municipality = municipality_emails["municipality"]
        emails = municipality_emails["emails"]
        html_message = WeeklyEMailService.__render_html_content(
            municipality, len(emails)
        )
        return (
            SUBJECT_TEMPLATE.format(
                municipality_name=municipality.name,
                date=timezone.now().strftime(date_format),
            ),
            html_message,
            SENDER,
            emails,
        )
