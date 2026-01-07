from uuid import uuid4
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.interfaces import ProjectRepository
from app.models.project import Project


class ProjectService:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def create_project(self, project: Project) -> str:
        project_id = uuid4().hex
        project.id = project_id
        await self.project_repo.save(project)
        return project_id

    async def update_project(self, project: Project) -> None:
        await self.project_repo.update(project)

    async def get_project_by_id(
        self, project_id: str
    ) -> Project:
        project = await self.project_repo.get(project_id)
        if not project:
            raise AppException(AppErr.PROJECT_NOT_FOUND)
        return project

    async def get_all_projects(self) -> list[Project]:
        return await self.project_repo.get_all()
