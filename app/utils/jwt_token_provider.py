import time
import jwt
from app.models.user import UserClaims


class JWTTokenProvider:
    def __init__(self,
                 jwt_secret: str,
                 issuer="https://api.watchexpense.com",
                 audience="https://api.watchexpense.com",
                 algorithm="HS256"):
        self._jwt_secret = jwt_secret
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience

    def generate_token(self, user_claims: UserClaims) -> str:
        claims = {
            "iss":     self._issuer,
            "aud":     self._audience,
            "iat":     int(time.time()),
            "exp":     int(time.time()) + 86400,  # 24 hours
            "sub":     user_claims.user_id,
            **user_claims.model_dump(),
        }
        return jwt.encode(claims,
                          self._jwt_secret, algorithm=self._algorithm)

    def vaidate_token(self, token: str) -> UserClaims:
        claims = jwt.decode(
            token, self._jwt_secret, algorithms=[self._algorithm])
        user_claims = UserClaims.model_validate(**claims, extra="ignore")
        return user_claims
