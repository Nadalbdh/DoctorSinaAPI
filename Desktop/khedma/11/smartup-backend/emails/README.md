# Emails

This application takes care of sending emails. It serves two main purposes:

- It helps manage mailing lists, by persisting them in the database (through the `Email` model) with the corresponding views.
- It provides abstractions to send emails, through different email services.

## Email services

The building block of all services is `BaseEMailService` which provides a skeleton to the other services:

- `get_mail_object`: returns _what_ we send in the email. This can be an object, a collection of objects, or anything else. Some concretizations expect certain return types
- `get_subject`: returns the subject of the email, depending on the mail object
- `get_recipients`: returns a list of emails
- `should_send`: determine whether the email should be sent depending on the mail object and the list of recipients
- `get_template_params`: maps the mail object to the template parameters. The template itself is defined as class field
- `send`: pipes the different functions together

Abstract implementations of this interface are also included:

- `PerCollectionEMailService`: fetches a collection of objects, and sends one email about all of them
- `PerObjectEMailService`: fetches a collection of objects, and sends one email about each one of them
- `OneObjectEMailService`: fetches one object, and sends an email about it. Implementations for `get_mail_object` are allowed to raise `ObjectDoesNotExist` exception, in which case nothing is sent.

These services take care of the `send` method. The idea is to have concrete services focus on *what* to send, not on how to send it.
