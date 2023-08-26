import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from backend.models import Citizen, Committee, Manager, Municipality


# TODO Refactor this into backend/baker_recipes.py and use model_bakery. Significantly less boilerplate code,
# Use factory.Faker() for random fake values inside the factory
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True


class ManagerFactory(DjangoModelFactory):
    class Meta:
        model = Manager

    user = factory.SubFactory(UserFactory)
    municipality = factory.Iterator(Municipality.objects.all())


class CitizenFactory(DjangoModelFactory):
    class Meta:
        model = Citizen

    user = factory.SubFactory(UserFactory)
    preferred_municipality = factory.Iterator(Municipality.objects.all())
    registration_municipality = factory.Iterator(Municipality.objects.all())


class CommitteeFactory(DjangoModelFactory):
    class Meta:
        model = Committee

    municipality = factory.Iterator(Municipality.objects.all())
    title = factory.Faker("sentence")
    body = factory.Faker("paragraph")
