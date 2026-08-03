import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from gating import process_code_submission
from models import ChatSession
from schemas.verify import VerifyCodeRequest, VerifyCodeResponse

router = APIRouter()


@router.post("/verify-code", response_model=VerifyCodeResponse, operation_id="verifyCode")
def post_verify_code(
    request: VerifyCodeRequest, db: Session = Depends(get_db)
) -> VerifyCodeResponse:
    session = db.get(ChatSession, request.session_id)
    if session is None or session.state != "awaiting_code":
        return VerifyCodeResponse(
            session_id=request.session_id,
            verified=False,
            state=session.state if session else "anonymous",
            message="There's no verification code pending for this session.",
        )

    verified, message = process_code_submission(session, request.code)

    # Recorded distinctly from a normal chat turn (not appended as a
    # "role": "user" message containing the raw code) so the transcript
    # doesn't grow a stray 6-digit chat bubble alongside the real
    # conversation (Section 4.6's transcript shape is flexible on role names).
    now = datetime.datetime.utcnow().isoformat()
    session.transcript = session.transcript + [
        {"role": "system", "content": "[verification code submitted]", "timestamp": now},
        {"role": "assistant", "content": message, "timestamp": now},
    ]

    db.commit()
    db.refresh(session)

    return VerifyCodeResponse(
        session_id=session.id,
        verified=verified,
        state=session.state,
        message=message,
    )
