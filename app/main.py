from fastapi import FastAPI
from uvicorn import run


app = FastAPI()


@app.get('/health')
def health_check():
    return "OK"


# initialization and setup...


def main():
    print("Running server with Uvicorn")
    run(app)


if __name__ == "__main__":
    main()
