from emails.services.reminder_emails_service.configuration_based_service import (
    ReminderComplaintProcessingEmail,
    ReminderComplaintReceivedEmail,
    ReminderDossierProcessingEmail,
    ReminderSubjectAccessReceivedEmail,
)
from emails.services.reminder_emails_service.interval_based_services import (
    ReminderDossierEmail,
    ReminderEventEmail,
    ReminderNewsEmail,
    ReminderReportEmail,
)

COMPLAINT_RECEPTION_INTERVAL_REMINDER = [
    {"days": 3, "msg": "أول"},
    {"days": 10, "msg": "ثاني"},
    {"days": 17, "msg": "نهائي"},
]
COMPLAINT_IN_PROCESS_INTERVAL_REMINDER = [
    {"days": 7, "msg": "أول"},
    {"days": 21, "msg": "ثاني"},
    {"days": 49, "msg": "ثالث"},
    {"days": 97, "msg": "رابع"},
    {"days": 193, "msg": "خامس"},
    {"days": 385, "msg": "نهائي"},
]
DOSSIER_INTERVAL_REMINDER = [
    {"days": 14, "msg": "أول"},
    {"days": 28, "msg": "ثاني"},
    {"days": 42, "msg": "ثالث"},
    {"days": 56, "msg": "رابع"},
    {"days": 70, "msg": "خامس"},
    {"days": 84, "msg": "نهائي"},
]
SUBJECT_ACCESS_RECEPTION_INTERVAL_REMINDER = [
    {"days": 2, "msg": "أول"},
    {"days": 8, "msg": "ثاني"},
    {"days": 14, "msg": "ثالث"},
    {"days": 20, "msg": "نهائي"},
]

NEWS_INTERVAL = 7

REPORT_INTERVAL = 28

DOSSIER_INTERVAL = 14

EVENT_INTERVAL = 14


class ReminderEmailHandler:
    """
    This class is used to reassemble daily, weekly , q2w reminders to make it more clear
    """

    def __init__(self, municipality):
        self.municipality = municipality

    def send_daily_reminder(self):
        """
        Send reminder daily : ( Complaint , Subject access request, Dossier )
        !!!__NB__!!!
        Keep the order because it affects the tests
        """
        self.__send_configuration(
            ReminderComplaintReceivedEmail, COMPLAINT_RECEPTION_INTERVAL_REMINDER
        )

        self.__send_configuration(
            ReminderComplaintProcessingEmail, COMPLAINT_IN_PROCESS_INTERVAL_REMINDER
        )

        self.__send_configuration(
            ReminderSubjectAccessReceivedEmail,
            SUBJECT_ACCESS_RECEPTION_INTERVAL_REMINDER,
        )

        self.__send_configuration(
            ReminderDossierProcessingEmail, DOSSIER_INTERVAL_REMINDER
        )

    def send_weekly_reminder(self):
        """
        Send reminder weekly : ( News )
        !!!__NB__!!!
        Keep the order because it affects the tests
        """
        ReminderNewsEmail(municipality=self.municipality, interval=NEWS_INTERVAL).send()

    def send_q2w_reminder(self):
        """
        Send reminder q2w : ( Event, Report, Dossier)
        !!!__NB__!!!
        Keep the order because it affects the tests
        """
        ReminderEventEmail(
            municipality=self.municipality, interval=EVENT_INTERVAL
        ).send()
        ReminderReportEmail(
            municipality=self.municipality, interval=REPORT_INTERVAL
        ).send()
        ReminderDossierEmail(
            municipality=self.municipality, interval=DOSSIER_INTERVAL
        ).send()

    def __send_configuration(self, klass, conf):
        for line in conf:
            klass(self.municipality, line["days"], line["msg"]).send()
