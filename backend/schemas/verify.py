from uuid import UUID

from pydantic import BaseModel, Field


class VerifyCodeRequest(BaseModel):
    session_id: UUID
    # Codes are 6 digits; a generous cap (not an exact-length/digits-only
    # constraint) still rejects an absurdly large pasted payload while
    # leaving the actual match logic in check_verification_code() as the
    # single source of truth for what counts as a valid code.
    code: str = Field(min_length=1, max_length=20)


class VerifyCodeResponse(BaseModel):
    session_id: UUID
    verified: bool
    state: str
    message: str
