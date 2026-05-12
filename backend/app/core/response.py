from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


def success_response(data: Any = None, message: str = "success") -> dict:
    return APIResponse(code=0, message=message, data=data).model_dump()


def error_response(message: str, code: int = 500, data: Any = None) -> dict:
    return APIResponse(code=code, message=message, data=data).model_dump()
