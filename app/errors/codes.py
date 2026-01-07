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
    THROTTLE = 1009

    # Auth errors
    INVALID_USER_CREDENTIAL = 2001
    ADMIN_ONLY = 2002

    # User resource errors
    CREATE_USER_PASSWORD_REQUIRED = 3001
    USER_ALREADY_EXISTS = 3002
    CANNOT_DELETE_SELF = 3003

    # Project resource errors
    PROJECT_ALREADY_EXISTS = 4001
    # Department resource error
    DEPARTMENT_ALREADY_EXISTS = 5001
    # Expense resource error
    EXPENSE_ALREADY_EXISTS = 6001
    # Advance resource error
    ADVANCE_ALREADY_EXISTS = 7001
