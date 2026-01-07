from dataclasses import dataclass
import enum


class AppErr(enum.IntEnum):
    NOT_FOUND = 1001
    UNAUTHORIZED = 1002
    FORBIDDEN = 1003
    CONFLICT = 1004
    INVALID = 1005
    INTERNAL = 1006
    TIMEOUT = 1007
    TOO_LARGE = 1008

    # Auth errors
    INVALID_USER_CREDENTIAL = 2001
    ADMIN_ONLY = 2002

    # User resource errors
    CREATE_USER_PASSWORD_REQUIRED = 3001
    USER_ALREADY_EXISTS = 3002
    CANNOT_DELETE_SELF = 3003

    # Project resource errors
    # Department resource error
    # Expense resource error
    # Advance resource error


@dataclass
class HTTPAppError:
    http_status: int
    message: str


def get_http_app_error(err_code: AppErr) -> HTTPAppError:
    return HTTPAppError(http_status=err_code, message=f"{err_code} - custom error message")
