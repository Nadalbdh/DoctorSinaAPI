class NotificationActionTypes:
    OPEN_SUBJECT = "OPEN_SUBJECT"
    OPEN_URL = "OPEN_URL"
    ETICKET_RESERVATION = "ETICKET_RESERVATION"

    @staticmethod
    def get_choices():
        return (
            (
                NotificationActionTypes.OPEN_SUBJECT,
                "Open Subject (comment, complaint, subject-access-request, dossier)",
            ),
            (NotificationActionTypes.OPEN_URL, "Open url"),
            (NotificationActionTypes.ETICKET_RESERVATION, "Digital Reservation"),
        )
