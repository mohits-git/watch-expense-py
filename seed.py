import asyncio
from uuid import uuid4
from boto3.resources.base import boto3
from app.models.user import User, UserRole
from app.repository.user_repository import UserRepository
from app.infra.bcrypt_password_hasher import BcryptPasswordHasher
import os

if os.getenv("ENVIRONMENT") != "production":
    from dotenv import load_dotenv
    load_dotenv()


admin_email = os.getenv("ADMIN_EMAIL_SEED")  or "admin@watchexpense.com"
admin_password = os.getenv("ADMIN_PASSWORD_SEED")  or "password"


async def seed():
    ddb_table_name = "watch-expense-py-table"
    session = boto3.Session(region_name="ap-south-1")
    resource = session.resource("dynamodb")
    table = resource.Table(ddb_table_name)

    user_repository = UserRepository(
        ddb_table=table,
        table_name=ddb_table_name
    )

    bcrypt_hasher = BcryptPasswordHasher()

    user_password = bcrypt_hasher.hash_password(admin_password)

    user = User(
        UserID=uuid4().hex,
        EmployeeID="EMP001",
        Name="Admin User",
        PasswordHash=user_password,
        Email=admin_email,
        Role=UserRole.Admin,
        ProjectID="",
        DepartmentID="",
    )
    await user_repository.save(user)
    print("Successfully seeded")

if __name__ == "__main__":
    asyncio.run(seed())
