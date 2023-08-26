from rest_framework.status import (
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class CustomError(Exception):
    ERROR_STATUS = HTTP_500_INTERNAL_SERVER_ERROR
    ERROR_MESSAGE = "An error occurred"


class InconsistentCategoriesError(CustomError):
    ERROR_STATUS = HTTP_400_BAD_REQUEST
    ERROR_MESSAGE = "Category and Sub-Category mismatch"


class InconsistentRegionError(CustomError):
    ERROR_STATUS = HTTP_400_BAD_REQUEST
    ERROR_MESSAGE = "Region does not match complaint"


class DeprecatedUsername(CustomError):
    ERROR_STATUS = HTTP_400_BAD_REQUEST
    ERROR_MESSAGE = "Attribute: 'username' is no longer used, Please remove it and use 'phone_number' instead"


class AccountCannotBeDeletedError(CustomError):
    ERROR_STATUS = HTTP_406_NOT_ACCEPTABLE
    ERROR_MESSAGE = "This user cannot be deleted"


class IncorrectSignatureError(CustomError):
    ERROR_STATUS = HTTP_400_BAD_REQUEST
    ERROR_MESSAGE = "This signature is incorrect"


class NotOwner(CustomError):
    ERROR_STATUS = HTTP_401_UNAUTHORIZED
    ERROR_MESSAGE = "This user is not authorized to retrieve an object"


class NotHandledLocally(CustomError):
    ERROR_STATUS = HTTP_202_ACCEPTED
    ERROR_MESSAGE = "could't cancel eticket locally."
