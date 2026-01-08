import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.dtos.response import ErrorResponse
from app.errors.app_exception import AppException
from app.errors.mapping import ERROR_MAP
from app.lifespan import lifespan
from app.routers.auth import auth_router
from app.routers.user import user_router
from app.routers.project import project_router
from app.routers.department import department_router
from app.routers.expense import expense_router
from app.routers.advance import advance_router
from app.routers.image import image_router


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(department_router, prefix="/api")
app.include_router(expense_router, prefix="/api")
app.include_router(advance_router, prefix="/api")
app.include_router(image_router, prefix="/api")

origins = [
    "https://watchexpense.mohits.me",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    http_status, default_msg = ERROR_MAP.get(
        exc.err_code, (500, "Unknown error"))
    # TODO: remove after dev
    print(exc.err_code, exc.message, exc.cause, http_status, default_msg)
    return JSONResponse(
        status_code=http_status,
        content=ErrorResponse(
            status=exc.err_code.value,
            message=exc.message or default_msg
        ).model_dump()
    )


if __name__ == "__main__":
    uvicorn.run(app)
