from typing import Annotated

from fastapi import Depends, HTTPException, Header, status

from app.dependencies.token_provider import TokenProviderInstance
from app.models.user import UserClaims, UserRole


def get_auth_token(
        authorization: Annotated[str | None, Header(alias="Authorization")],
        token_provider: TokenProviderInstance) -> str:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized")
    try:
        token = authorization.split(' ', 2)[1]
        claims = token_provider.validate_token(token)
        if not claims:
            raise Exception("Unauthorized")
        return token
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized")


AuthTokenHeader = Annotated[str, Depends(get_auth_token)]


def get_authenticated_user(token: AuthTokenHeader, token_provider: TokenProviderInstance) -> UserClaims:
    return token_provider.validate_token(token)


AuthenticatedUser = Annotated[UserClaims, Depends(get_authenticated_user)]


def admin_only(curr_user: AuthenticatedUser):
    if curr_user.role != UserRole.Admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden")


def employee_only(curr_user: AuthenticatedUser):
    if curr_user.role != UserRole.Employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden")
