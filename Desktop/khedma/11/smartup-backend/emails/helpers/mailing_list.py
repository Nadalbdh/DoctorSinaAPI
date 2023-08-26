from emails.models import Email


def update_mailing_list(municipality, new_mailing_list, append=False):
    """
    If append is set to true, add the new mailing list to the existing one
    """
    if not append:
        municipality.emails.exclude(email__in=new_mailing_list).delete()
    municipality_emails = [entry.email for entry in municipality.emails.all()]
    to_add = [
        Email(email=email, municipality=municipality)
        for email in new_mailing_list
        if email not in municipality_emails
    ]
    Email.objects.bulk_create(to_add)
