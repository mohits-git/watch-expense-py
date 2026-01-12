import asyncio
from uuid import uuid4
from boto3.resources.base import boto3
from app.models.user import User, UserRole
from app.repository.user_repository import UserRepository
from app.infra.bcrypt_password_hasher import BcryptPasswordHasher


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

    user_password = bcrypt_hasher.hash_password("password")

    user = User(
        UserID=uuid4().hex,
        EmployeeID="EMP001",
        Name="Admin User",
        PasswordHash=user_password,
        Email="admin@watchexpense.com",
        Role=UserRole.Admin,
        ProjectID="",
        DepartmentID="",
    )
    await user_repository.save(user)
    print("Successfully seeded")

if __name__ == "__main__":
    asyncio.run(seed())
