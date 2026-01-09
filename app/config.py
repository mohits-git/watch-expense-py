import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    environment: str = ""
    dynamodb_table: str = ""
    jwt_secret: str = ""
    jwt_issuer: str = ""
    jwt_audience: str = ""
    upload_directory: str = ""
    s3_bucket_name: str = ""


def _get_env(name: str) -> str:
    return os.getenv(name) or ""


_config = None


def load_config() -> Config:
    global _config
    if not _config:
        load_dotenv()
        _config = Config(
            environment=_get_env("ENVIRONMENT"),
            dynamodb_table=_get_env("DYNAMODB_TABLE"),
            jwt_secret=_get_env("JWT_SECRET"),
            jwt_issuer=_get_env("JWT_ISSUER"),
            jwt_audience=_get_env("JWT_AUDIENCE"),
            upload_directory=_get_env("UPLOAD_DIRECTORY"),
            s3_bucket_name=_get_env("S3_BUCKET_NAME"),
        )
    return _config
