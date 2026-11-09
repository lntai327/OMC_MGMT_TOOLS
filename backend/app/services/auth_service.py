from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.core.security import verify_password, create_access_token, get_password_hash
from app.schemas.auth import LoginRequest, Token, UserCreate


class AuthService:
    async def authenticate_user(self, session: AsyncSession, creds: LoginRequest) -> Token:
        user = await user_repo.get_by_username(session, creds.username)
        if not user or not verify_password(creds.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )

        token = create_access_token(subject=user.username, role=user.role)
        return Token(access_token=token, token_type="bearer", role=user.role, username=user.username)

    async def register_user(self, session: AsyncSession, user_in: UserCreate) -> User:
        existing = await user_repo.get_by_username(session, user_in.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        new_user = await user_repo.create(
            session,
            {
                "username": user_in.username,
                "hashed_password": get_password_hash(user_in.password),
                "role": user_in.role,
                "is_active": True,
            }
        )
        return new_user


auth_service = AuthService()

