from app.errors.codes import AppErr


class AppException(Exception):
    def __init__(self,
                 err_code: AppErr,
                 msg: str | None = None,
                 *,
                 cause: Exception | None = None) -> None:
        self.err_code = err_code
        self.message = msg
        self.cause = cause
