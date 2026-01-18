from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import LoginRequest, TokenResponse, UserOut
from src.services.audit import write_audit
from src.services.auth import authenticate_user, create_user_token, get_user_roles
from src.shared.errors import AppError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        write_audit(
            db,
            request.state.request_id,
            action="AUTH_LOGIN_FAIL",
            payload={"email": payload.email},
        )
        raise AppError("AUTH_INVALID", "Invalid email or password.", 401)

    token = create_user_token(user)
    write_audit(
        db,
        request.state.request_id,
        action="AUTH_LOGIN_SUCCESS",
        actor_user_id=str(user.id),
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        roles=get_user_roles(user),
    )