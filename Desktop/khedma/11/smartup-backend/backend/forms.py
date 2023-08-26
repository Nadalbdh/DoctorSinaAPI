from django import forms
from django.core.validators import RegexValidator
from django.forms import TextInput

from backend.models import Municipality
from backend.validators import validate_digits


class PhoneNumberFormField(forms.CharField):
    def validate(self, value):
        validate_digits(value, forms.ValidationError)


class BootstrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


coordinates_validator = RegexValidator(
    r"^(-?\d{2}\.\d+),\s*(-?\d{1,2}\.\d+)$", "Coordinates need to be valid."
)


class MunicipalityOnboardingForm(BootstrapForm):
    coordinates = forms.CharField(
        widget=TextInput(attrs={"pattern": r"^(-?\d{2}\.\d+),\s*(-?\d{1,2}\.\d+)$"}),
        validators=[coordinates_validator],
        help_text="latitude, longitude (ex:35.67710, 9.88049)",
    )
    municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.all().filter(is_active=False)
    )
    municipality_name_fr = forms.CharField()
    logo = forms.ImageField(help_text="Warning: Make sure the logo is a square")
    website = forms.URLField(
        required=False, help_text="For example: https://www.commune-gremda.com/"
    )
    facebook_url = forms.URLField(required=False)
    manager_fullname = forms.CharField(help_text="Warning: Use Arabic")
    manager_number = PhoneNumberFormField(max_length=8, min_length=8)
    manager_title = forms.CharField(help_text="Warning: Use Arabic")
    manager_email = forms.EmailField()
    operation = forms.CharField(widget=forms.HiddenInput())

    title = "Municipality Onboarding"
    help_text = """
    Use this form to add the needed attributes for the municipality and activate a manager's account with full permissions.
    <ul>
    <li>
    You can choose to activate a municipality using this form, or do it later with the activation form (use the navigation bar).
    </li>
    <li>
    A password for the manager's account will be generated. <strong>This will not be saved on the server</strong>, so make sure to save the password. Make sure to advise the manager to change this password, so it is personal for them.
    </li>
    </ul>
    """


class MunicipalityActivationForm(BootstrapForm):
    inactive_municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.all().filter(is_active=False), required=False
    )
    operation = forms.CharField(widget=forms.HiddenInput())
    active_municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.all().filter(is_active=True), required=False
    )
    title = "Municipality Activation"
    help_text = "Use this form to sign contract/activate a municipality. The onboarding must be executed beforehand"
