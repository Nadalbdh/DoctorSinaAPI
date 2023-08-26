from model_bakery import baker

from backend.tests.test_utils import force_date_attribute, set_and_save_date

# TODO move all bakery things here


def add_status(obj, status, status_date, full_time=False):
    """
    Adds a status to the updatable object with the given date
    """
    if full_time:
        return set_and_save_date(
            obj.operation_updates.create(status=status), status_date
        )

    return force_date_attribute(
        obj.operation_updates.create(status=status), status_date
    )


def bake_updatable(model, date, status, status_date, municipality, **kwargs):
    """
    Creates the updatable object with the given status.
    """
    updatable_object = force_date_attribute(
        baker.make(model, municipality=municipality, **kwargs), date
    )
    # patch created_at for the first update
    force_date_attribute(updatable_object.operation_updates.first(), date)
    add_status(updatable_object, status, status_date)
    return updatable_object


def bake_updatable_full_time(model, date, status, status_date, municipality, **kwargs):
    """
    Creates the updatable object with the given status.
    """
    updatable_object = set_and_save_date(
        baker.make(model, municipality=municipality, **kwargs), date
    )
    # patch created_at for the first update
    set_and_save_date(updatable_object.operation_updates.first(), date)
    add_status(updatable_object, status, status_date, True)
    return updatable_object
