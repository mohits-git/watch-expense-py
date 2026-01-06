from typing import Any
from pydantic import BaseModel


class BaseResponse(BaseModel):
    status: int
    message: str
    data: Any | None
