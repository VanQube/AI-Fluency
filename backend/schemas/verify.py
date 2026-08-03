from uuid import UUID

from pydantic import BaseModel


class VerifyCodeRequest(BaseModel):
    session_id: UUID
    code: str


class VerifyCodeResponse(BaseModel):
    session_id: UUID
    verified: bool
    state: str
    message: str
