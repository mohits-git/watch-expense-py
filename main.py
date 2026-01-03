from app.app import app
from uvicorn import run


def main():
    print("Running server with Uvicorn")
    run(app)


if __name__ == "__main__":
    main()
