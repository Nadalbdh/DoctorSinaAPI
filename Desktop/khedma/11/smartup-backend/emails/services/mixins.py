from emails.utils import get_managers_emails_by_permission_per_municipality

"""
A set of mixins to be used with email services
"""


class PermissionBasedRecipientsMixin:
    """
    Provides a `get_recipients` function that returns the emails of
    the managers having the specified permission
    """

    def get_recipients(self):
        return get_managers_emails_by_permission_per_municipality(
            self.municipality, self.permission
        )
