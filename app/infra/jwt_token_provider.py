import time
import jwt
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
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

    def validate_token(self, token: str) -> UserClaims:
        try:
            claims = jwt.decode(
                token, self._jwt_secret,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
            )
            user_claims = UserClaims.model_validate(claims, extra="ignore")
            return user_claims
        except jwt.ExpiredSignatureError as err:
            raise AppException(AppErr.TOKEN_EXPIRED, cause=err)
        except jwt.InvalidSignatureError as err:
            raise AppException(AppErr.TOKEN_INVALID_SIGNATURE, cause=err)
        except jwt.InvalidAudienceError as err:
            raise AppException(AppErr.TOKEN_INVALID_AUDIENCE, cause=err)
        except jwt.InvalidIssuerError as err:
            raise AppException(AppErr.TOKEN_INVALID_ISSUER, cause=err)
        except (jwt.DecodeError, jwt.InvalidTokenError) as err:
            raise AppException(AppErr.TOKEN_DECODE_ERROR, cause=err)
