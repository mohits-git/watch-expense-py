from app.models.user import UserClaims
import jwt


class JWTTokenProvider:
    def __init__(self, jwt_secret: str, algorithm="HS256"):
        self._jwt_secret = jwt_secret
        self._algorithm = algorithm

    def generate_token(self, user_claims: UserClaims) -> str:
        # TODO: create claims
        claims = user_claims
        return jwt.encode(claims,
                          self._jwt_secret, algorithm=self._algorithm)

    def vaidate_token(self, token: str) -> UserClaims:
        claims = jwt.decode(
            token, self._jwt_secret, algorithms=[self._algorithm])
        # TODO: parse user claims
        return claims
