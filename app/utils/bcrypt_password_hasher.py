import bcrypt


class BcryptPasswordHasher:
    def __init__(self, cost: int = 12):
        self._cost = cost

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(self._cost)).decode('utf-8')

    def verify_password(self, password_hash: str, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8'))
