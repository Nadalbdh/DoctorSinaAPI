from ast import literal_eval


def cast_dict(value):
    """
    Helper to convert config values to dictionaries.
    """
    value = str(value)

    try:
        assert value.startswith("{")  # sanity check
        assert value.endswith("}")

        dic = literal_eval(value)
    except AssertionError:
        dic = None
    return dic


def cast_list(value):
    """
    Helper to convert config values to lists.
    """
    value = str(value)

    try:
        assert value.startswith("[")  # sanity check
        assert value.endswith("]")

        xs = literal_eval(value)
    except AssertionError:
        xs = None
    return xs
