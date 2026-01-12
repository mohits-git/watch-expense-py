from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.dtos.response import ErrorResponse
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.errors.mapping import ERROR_MAP


async def app_exception_handler(request: Request, exc):
    http_status, default_msg = ERROR_MAP.get(
        exc.err_code, (500, "Unknown error"))
    print("ERROR: ", exc.cause)
    return JSONResponse(
        status_code=http_status,
        content=ErrorResponse(
            status=exc.err_code.value,
            message=exc.message or default_msg
        ).model_dump()
    )


async def request_validation_exception_handler(request: Request, exc):
    err_msg = "Invalid Request\nValidation errors:"
    for error in exc.errors():
        err_msg += f"\nField: {error['loc']}, Error: {error['msg']}"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            status=AppErr.VALIDATION,
            message=err_msg,
        ).model_dump()
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(AppException,
                              app_exception_handler)
    app.add_exception_handler(RequestValidationError,
                              request_validation_exception_handler)
