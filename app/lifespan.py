from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.repository.department_repository import DepartmentRepository
from app.repository.expense_repository import ExpenseRepository
from app.repository.advance_repository import AdvanceRepository
from app.repository.user_repository import UserRepository
from app.repository.project_repository import ProjectRepository
from app.repository.image_metadata_repository import ImageMetadataRepository
from app.repository import get_boto3_session
from app.services.auth import AuthService
from app.services.image import ImageService
from app.services.user import UserService
from app.services.project import ProjectService
from app.services.department import DepartmentService
from app.services.expense import ExpenseService
from app.services.advance import AdvanceService
from app.infra.bcrypt_password_hasher import BcryptPasswordHasher
from app.infra.jwt_token_provider import JWTTokenProvider
from app.infra.s3_image_store import S3ImageStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ddb_resource
    session = get_boto3_session()
    try:
        async with (
            session.resource("dynamodb") as dynamodb_resource,
            session.client("s3") as s3_client
        ):
            # ddb
            table_name = "watch-expense-table"
            ddb_table = await dynamodb_resource.Table(table_name)
            # repos
            user_repo = UserRepository(ddb_table, table_name)
            project_repo = ProjectRepository(ddb_table, table_name)
            department_repo = DepartmentRepository(ddb_table, table_name)
            expense_repo = ExpenseRepository(ddb_table, table_name)
            advance_repo = AdvanceRepository(ddb_table, table_name)
            image_metadata_repo = ImageMetadataRepository(ddb_table, table_name)

            # infra
            token_provider = JWTTokenProvider('top-secret')
            password_hasher = BcryptPasswordHasher()

            bucket_name = "watch-expense-bucket"
            image_store = S3ImageStore(bucket_name, s3_client)

            # services
            auth_service = AuthService(
                user_repo, token_provider, password_hasher)
            user_service = UserService(
                password_hasher, user_repo, project_repo)
            project_service = ProjectService(project_repo)
            department_service = DepartmentService(department_repo)
            expense_service = ExpenseService(expense_repo, advance_repo)
            advance_service = AdvanceService(advance_repo)
            image_service = ImageService(image_metadata_repo, image_store)

            # add to state
            app.state.token_provider = token_provider
            app.state.auth_service = auth_service
            app.state.user_service = user_service
            app.state.project_service = project_service
            app.state.department_service = department_service
            app.state.expense_service = expense_service
            app.state.advance_service = advance_service
            app.state.image_service = image_service
            yield
    except Exception as e:
        print("Error while starting up the server: ", e)
