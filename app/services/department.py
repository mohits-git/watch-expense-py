from uuid import uuid4
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.interfaces import DepartmentRepository
from app.models.department import Department


class DepartmentService:
    def __init__(self, department_repo: DepartmentRepository):
        self.department_repo = department_repo

    async def create_department(self, department: Department) -> str:
        department_id = uuid4().hex
        department.id = department_id
        await self.department_repo.save(department)
        return department_id

    async def update_department(self, department: Department) -> None:
        await self.department_repo.update(department)

    async def get_department_by_id(
        self, department_id: str
    ) -> Department:
        department = await self.department_repo.get(department_id)
        if not department:
            raise AppException(AppErr.DEPARTMENT_NOT_FOUND)
        return department

    async def get_all_departments(self) -> list[Department]:
        return await self.department_repo.get_all()
