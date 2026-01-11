import time
from uuid import uuid4
import pytest
import jwt
from app.errors.app_exception import AppException
from app.errors.codes import AppErr
from app.infra.jwt_token_provider import JWTTokenProvider
from app.models.user import UserClaims, UserRole


class TestJWTTokenProvider:
    @pytest.fixture
    def jwt_secret(self):
        return "test_secret_key_for_testing_purposes"

    @pytest.fixture
    def token_provider(self, jwt_secret):
        return JWTTokenProvider(
            jwt_secret=jwt_secret,
            issuer="https://api.watchexpense.com",
            audience="https://api.watchexpense.com",
            algorithm="HS256"
        )

    @pytest.fixture
    def sample_user_claims(self):
        return UserClaims(
            id=uuid4().hex,
            name="Test User",
            email="test@example.com",
            role=UserRole.Employee
        )

    def test_generate_token_success(self, token_provider, sample_user_claims):
        token = token_provider.generate_token(sample_user_claims)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_generate_token_contains_claims(self, token_provider, sample_user_claims, jwt_secret):
        token = token_provider.generate_token(sample_user_claims)

        decoded = jwt.decode(token, jwt_secret,
                             algorithms=["HS256"],
                             issuer="https://api.watchexpense.com",
                             audience="https://api.watchexpense.com")

        assert decoded["sub"] == sample_user_claims.user_id
        assert decoded["name"] == sample_user_claims.name
        assert decoded["email"] == sample_user_claims.email
        assert decoded["role"] == sample_user_claims.role
        assert decoded["iss"] == "https://api.watchexpense.com"
        assert decoded["aud"] == "https://api.watchexpense.com"
        assert "iat" in decoded
        assert "exp" in decoded

    def test_generate_token_expiration(self, token_provider, sample_user_claims, jwt_secret):
        before_time = int(time.time())
        token = token_provider.generate_token(sample_user_claims)
        after_time = int(time.time())

        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"],
                             issuer="https://api.watchexpense.com",
                             audience="https://api.watchexpense.com")

        expected_exp = before_time + 86400
        assert decoded["exp"] >= expected_exp
        assert decoded["exp"] <= after_time + \
            86400 + 1

    def test_generate_token_different_roles(self, token_provider):
        admin_claims = UserClaims(
            id=uuid4().hex,
            name="Admin User",
            email="admin@example.com",
            role=UserRole.Admin
        )

        token = token_provider.generate_token(admin_claims)
        validated_claims = token_provider.validate_token(token)

        assert validated_claims.role == UserRole.Admin

    def test_validate_token_success(self, token_provider, sample_user_claims):
        token = token_provider.generate_token(sample_user_claims)

        validated_claims = token_provider.validate_token(token)

        assert validated_claims.user_id == sample_user_claims.user_id
        assert validated_claims.name == sample_user_claims.name
        assert validated_claims.email == sample_user_claims.email
        assert validated_claims.role == sample_user_claims.role

    def test_validate_token_expired(self, jwt_secret):
        token_provider = JWTTokenProvider(jwt_secret)

        expired_claims = {
            "iss": "https://api.watchexpense.com",
            "aud": "https://api.watchexpense.com",
            "iat": int(time.time()) - 100000,
            "exp": int(time.time()) - 1,
            "sub": uuid4().hex,
            "id": uuid4().hex,
            "name": "Test User",
            "email": "test@example.com",
            "role": UserRole.Employee,
        }
        expired_token = jwt.encode(
            expired_claims, jwt_secret, algorithm="HS256")

        with pytest.raises(AppException) as exc:
            token_provider.validate_token(expired_token)
        
        assert exc.value.err_code == AppErr.TOKEN_EXPIRED

    def test_validate_token_invalid_signature(self, token_provider, sample_user_claims):
        token = token_provider.generate_token(sample_user_claims)

        different_provider = JWTTokenProvider(jwt_secret="different_secret")

        with pytest.raises(AppException) as exc:
            different_provider.validate_token(token)
        
        assert exc.value.err_code == AppErr.TOKEN_INVALID_SIGNATURE

    def test_validate_token_wrong_audience(self, jwt_secret, sample_user_claims):
        provider1 = JWTTokenProvider(
            jwt_secret=jwt_secret,
            audience="https://api.watchexpense.com"
        )
        token = provider1.generate_token(sample_user_claims)

        provider2 = JWTTokenProvider(
            jwt_secret=jwt_secret,
            audience="https://different.audience.com"
        )

        with pytest.raises(AppException) as exc:
            provider2.validate_token(token)
        
        assert exc.value.err_code == AppErr.TOKEN_INVALID_AUDIENCE

    def test_validate_token_wrong_issuer(self, jwt_secret, sample_user_claims):
        provider1 = JWTTokenProvider(
            jwt_secret=jwt_secret,
            issuer="https://api.watchexpense.com"
        )
        token = provider1.generate_token(sample_user_claims)

        provider2 = JWTTokenProvider(
            jwt_secret=jwt_secret,
            issuer="https://different.issuer.com"
        )

        with pytest.raises(AppException) as exc:
            provider2.validate_token(token)
        
        assert exc.value.err_code == AppErr.TOKEN_INVALID_ISSUER

    def test_validate_token_malformed(self, token_provider):
        malformed_token = "this.is.not.a.valid.jwt"

        with pytest.raises(AppException) as exc:
            token_provider.validate_token(malformed_token)
        
        assert exc.value.err_code == AppErr.TOKEN_DECODE_ERROR

    def test_validate_token_empty_string(self, token_provider):
        with pytest.raises(AppException) as exc:
            token_provider.validate_token("")
        
        assert exc.value.err_code == AppErr.TOKEN_DECODE_ERROR

    def test_different_algorithm(self, jwt_secret, sample_user_claims):
        provider = JWTTokenProvider(
            jwt_secret=jwt_secret * 2,
            algorithm="HS512"
        )

        token = provider.generate_token(sample_user_claims)
        validated = provider.validate_token(token)

        assert validated.user_id == sample_user_claims.user_id