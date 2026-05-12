from pydantic import BaseModel
from typing import Optional


class MarkStudiedRequest(BaseModel):
    studied: bool


class FavoriteRequest(BaseModel):
    favorite: bool


class UserResourceProgressSchema(BaseModel):
    id: int
    user_id: int
    resource_id: int
    studied: bool
    favorite: bool

    class Config:
        from_attributes = True
