import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from backend.app.db import get_session
from backend.app.models import ApiKeyRecord, GenerateApiKeyRequest, GenerateApiKeyResponse

router = APIRouter(prefix="/api/v1/keys", tags=["keys"])


@router.post("", response_model=GenerateApiKeyResponse)
def generate_api_key(
    request: GenerateApiKeyRequest,
    session: Session = Depends(get_session),
):
    try:
        new_key_str = f"fs_live_{secrets.token_hex(16)}"
        record = ApiKeyRecord(
            id=f"key_{secrets.token_hex(8)}",
            key=new_key_str,
            name=request.name or "default",
            is_active=True,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        return GenerateApiKeyResponse(
            api_key=record.key,
            name=record.name,
            created_at=record.created_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "KEY_GEN_ERROR", "message": str(e)}},
        )
