from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserCreate, UserResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    creds = LoginRequest(username=form_data.username, password=form_data.password)
    return await auth_service.authenticate_user(session, creds)


@router.post("/login/json", response_model=Token)
async def login_json(
    creds: LoginRequest,
    session: AsyncSession = Depends(get_db)
):
    return await auth_service.authenticate_user(session, creds)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/register", response_model=UserResponse, dependencies=[Depends(require_roles(["admin"]))])
async def register_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db)
):
    return await auth_service.register_user(session, user_in)

