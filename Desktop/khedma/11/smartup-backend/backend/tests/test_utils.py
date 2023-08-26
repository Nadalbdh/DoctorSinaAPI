import random
from datetime import datetime

from django.utils.timezone import get_current_timezone
from faker import Faker

from factories import CitizenFactory

NUMBER_MUNICIPALITIES = 350

fake = Faker()


def get_random_municipality_id():
    return random.randint(1, NUMBER_MUNICIPALITIES)


def get_random_municipality_ids(n):
    choices = list(range(1, NUMBER_MUNICIPALITIES + 1))
    random.shuffle(choices)
    return choices[:n]


def check_equal_attributes(db_object, request_object, attributes):
    """
    Checks whether the given attributes are equal in the data base object and the given json representation.
    """
    for attr in attributes:
        if getattr(db_object, attr) != request_object[attr]:
            return False
    return True


def authenticate_citizen(api_client):
    """
    Authenticate a citizen and return corresponding user
    """
    citizen = CitizenFactory()
    api_client.force_authenticate(user=citizen.user)
    return citizen.user


def get_random_phone_number():
    numbers = [str(i) for i in [2, 3, 4, 7, 5, 9]]
    return "".join(fake.random_choices(numbers, 8))


def parse_date_aware(date: str, format="%Y-%m-%d"):
    # return date
    date_obj = datetime.strptime(date, format)
    return get_current_timezone().localize(date_obj)


def force_citizen_joined_at(citizen, date):
    return force_date_attribute(citizen.user, date, "date_joined")


def force_date_attribute(obj, date, attr_name="created_at"):
    setattr(obj, attr_name, parse_date_aware(date))
    obj.save()
    return obj


def set_and_save_date(obj, value, attr_name="created_at"):
    setattr(obj, attr_name, value)
    obj.save()
    return obj


def random_stream(seq):
    while True:
        yield random.choice(seq)


def get_db_choices(enum):
    return [f for (f, _) in enum.get_choices()]
