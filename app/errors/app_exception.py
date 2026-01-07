from app.errors.codes import AppErr


class AppException(Exception):
    def __init__(self, err_code: AppErr, msg: str | None = "Application error"):
        self.err_code = err_code
        self.message = msg
