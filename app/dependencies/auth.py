from typing import Annotated

from fastapi import Depends, HTTPException, Header, status

from app.dependencies.token_provider import TokenProviderInstance
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.models.user import UserClaims, UserRole


def auth_token(
    authorization: Annotated[str | None, Header(alias="Authorization")],
    token_provider: TokenProviderInstance,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    try:
        token = authorization.split(" ", 2)[1]
        claims = token_provider.validate_token(token)
        if not claims:
            raise AppException(AppErr.UNAUTHORIZED)
        return token
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )


AuthTokenHeader = Annotated[str, Depends(auth_token)]


def authenticated_user(
    token: AuthTokenHeader, token_provider: TokenProviderInstance
) -> UserClaims:
    return token_provider.validate_token(token)


AuthenticatedUser = Annotated[UserClaims, Depends(authenticated_user)]


def required_roles(roles: list[UserRole]):
    def required_roles_dependency(curr_user: AuthenticatedUser):
        if curr_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
            )
    return required_roles_dependency
