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
    s3_bucket_name: str = ""


_config = None


def load_config() -> Config:
    global _config
    if not _config:
        load_dotenv()
        _config = Config(
            environment=os.getenv("ENVIRONMENT") or "production",
            dynamodb_table=os.getenv("DYNAMODB_TABLE") or "watch-expense-table",
            jwt_secret=os.getenv("JWT_SECRET") or "YsQz/FBocPkAhbtLO1AzGQ6lG/hn14zw4ebMp+NToik=",
            jwt_issuer=os.getenv("JWT_ISSUER") or "https://api.watchexpense.mohits.me",
            jwt_audience=os.getenv("JWT_AUDIENCE") or "https://api.watchexpense.mohits.me",
            s3_bucket_name=os.getenv("S3_BUCKET_NAME") or "watch-expense-bucket",
        )
    return _config
