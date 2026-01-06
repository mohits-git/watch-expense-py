from app.errors.codes import AppErrCode


class AppException(Exception):
    def __init__(self,
                 exc_code: AppErrCode,
                 msg: str = "Internal Server Error"):
        self.status = exc_code
        self.message = msg
