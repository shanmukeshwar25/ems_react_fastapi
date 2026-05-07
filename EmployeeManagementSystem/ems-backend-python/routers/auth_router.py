"""Auth router — mirrors AuthController.java."""

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_role
from core.config import settings
from schemas.auth import LoginRequest, ChangePasswordDTO, PushTokenRequest
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    result = auth_service.login(db, req.username, req.password)
    response.set_cookie("access_token", result["token"],
                        httponly=True, secure=settings.cookie_secure,
                        samesite=settings.cookie_same_site, max_age=settings.jwt_access_expiration_ms // 1000)
    response.set_cookie("refresh_token", result["refreshToken"],
                        httponly=True, secure=settings.cookie_secure,
                        samesite=settings.cookie_same_site, max_age=settings.jwt_refresh_expiration_ms // 1000)
    return result


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    """Read the refresh token exclusively from the httpOnly cookie."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh_token cookie",
        )
    result = auth_service.refresh_token_fn(db, token)
    response.set_cookie(
        "access_token", result["token"],
        httponly=True, secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        max_age=settings.jwt_access_expiration_ms // 1000,
    )
    return {"message": "Token refreshed"}


@router.post("/logout")
def logout(response: Response):
    """Clear both httpOnly auth cookies."""
    response.delete_cookie("access_token",  httponly=True, samesite=settings.cookie_same_site)
    response.delete_cookie("refresh_token", httponly=True, samesite=settings.cookie_same_site)
    return {"message": "Logged out"}


@router.get("/me")
def me(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return auth_service.get_current_user_info(db, user["emp_id"])


@router.put("/changePassword")
def change_pw(req: ChangePasswordDTO, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service.change_password(db, user["emp_id"], req.oldPassword, req.newPassword)
    return {"message": "Password changed successfully"}


@router.put("/push-token")
def push_token(req: PushTokenRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service.save_push_token(db, user["emp_id"], req.pushToken)
    return {"message": "Push token saved"}


@router.post("/reset-password/{empId}")
def reset_pw(empId: str, user: dict = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    auth_service.reset_password(db, empId)
    return {"message": f"Password reset for {empId}"}
