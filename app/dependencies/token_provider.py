from typing import Annotated

from fastapi import Depends, Request

from app.interfaces.token_provider import TokenProvider


def get_token_provider(request: Request) -> TokenProvider:
    return request.app.state.token_provider


TokenProviderInstance = Annotated[TokenProvider, Depends(get_token_provider)]
