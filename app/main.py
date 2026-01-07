from fastapi import FastAPI
from uvicorn import run
from app.lifespan import lifespan
from app.routers.auth import auth_router
from app.routers.user import user_router
from app.routers.project import project_router
from app.routers.department import department_router
from app.routers.expense import expense_router
from app.routers.advance import advance_router


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(department_router, prefix="/api")
app.include_router(expense_router, prefix="/api")
app.include_router(advance_router, prefix="/api")


if __name__ == "__main__":
    print("Running server with Uvicorn")
    run(app)
