from contextlib import asynccontextmanager
from fastapi import FastAPI
from uvicorn import run

from app.repository import get_boto3_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ddb_resource
    session = get_boto3_session()
    async with session.resource("dynamodb") as dynamodb_resource:
        app.state.ddb_table = await dynamodb_resource.Table('watch-expense-table')
        yield
        app.state.ddb_table = None


app = FastAPI(lifespan=lifespan)


def main():
    print("Running server with Uvicorn")
    run(app)


if __name__ == "__main__":
    main()
