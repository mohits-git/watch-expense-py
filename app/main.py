import uvicorn
from fastapi import FastAPI
from app.lifespan import lifespan
from app.middleware import register_middlewares
from app.routers.auth import auth_router
from app.routers.user import user_router
from app.routers.project import project_router
from app.routers.department import department_router
from app.routers.expense import expense_router
from app.routers.advance import advance_router
from app.routers.image import image_router
from app.exception import register_exception_handlers


app = FastAPI(lifespan=lifespan)
register_middlewares(app)
register_exception_handlers(app)
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(department_router, prefix="/api")
app.include_router(expense_router, prefix="/api")
app.include_router(advance_router, prefix="/api")
app.include_router(image_router, prefix="/api")


@app.get('/health')
async def health_check():
    return "OK"


if __name__ == "__main__":
    uvicorn.run(app)
