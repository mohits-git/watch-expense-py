from fastapi import FastAPI
from uvicorn import run
from app.dependencies import lifespan
from app.routers.auth_router import auth_router


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix='/api')


if __name__ == "__main__":
    print("Running server with Uvicorn")
    run(app)
