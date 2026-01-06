import enum


class AppErrCode(enum.IntEnum):
    NOT_FOUND = 1001
    UNAUTHORIZED = 1002
    FORBIDDEN = 1003
    CONFLICT = 1004
    INVALID = 1005
    INTERNAL = 1006
    TIMEOUT = 1007
    TOO_LARGE = 1008
