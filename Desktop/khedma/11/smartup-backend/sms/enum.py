class SMSQueueStatus:
    SENT = "SENT"
    FAILED = "FAILED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"
    PENDING = "PENDING"  # Waiting for municipality activation

    @staticmethod
    def get_choices():
        return (
            (SMSQueueStatus.SENT, "SENT"),
            (SMSQueueStatus.FAILED, "FAILED"),
            (SMSQueueStatus.PENDING, "PENDING"),
            (SMSQueueStatus.TOO_MANY_ATTEMPTS, "TOO_MANY_ATTEMPTS"),
        )
