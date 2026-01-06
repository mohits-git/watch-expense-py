from app.errors.codes import AppErr


class AppException(Exception):
    def __init__(self,
                 exc_code: AppErr,
                 msg: str | None = "Application error"):
        super().__init__(msg)
        self.status = exc_code
        self.message = msg
