from fastapi import APIRouter, HTTPException, Cookie, Response
from pydantic import BaseModel
from access import authenticate
from auth import create_session, get_session, delete_session

router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest, response: Response):
    user = authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    token = create_session(user)
    response.set_cookie("session_token", token, httponly=True, samesite="strict")
    return {"rol": user.role, "name": user.name}


@router.post("/logout")
def logout(response: Response, session_token: str | None = Cookie(default=None)):
    if session_token:
        delete_session(session_token)
    response.delete_cookie("session_token")
    return {"ok": True}


@router.get("/me")
def me(session_token: str | None = Cookie(default=None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="No autenticado.")
    user = get_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión expirada.")
    return {"name": user.name, "rol": user.role}