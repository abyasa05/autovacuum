import bcrypt
from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.translation import gettext_noop as _

class CustomBcryptPasswordHasher(BasePasswordHasher):
    """
    Custom password hasher that purely uses bcrypt, without SHA256 pre-hashing.
    """
    algorithm = "custom_bcrypt"
    library = "bcrypt"

    def salt(self):
        return bcrypt.gensalt()

    def encode(self, password, salt):
        password_bytes = password.encode('utf-8')
        if isinstance(salt, str):
            salt_bytes = salt.encode('utf-8')
        else:
            salt_bytes = salt
            
        hashed = bcrypt.hashpw(password_bytes, salt_bytes)
        return f"{self.algorithm}${hashed.decode('utf-8')}"

    def verify(self, password, encoded):
        algorithm, hashed = encoded.split('$', 1)
        assert algorithm == self.algorithm
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def safe_summary(self, encoded):
        algorithm, hashed = encoded.split('$', 1)
        return {
            _('algorithm'): algorithm,
            _('hash'): self.mask_hash(hashed),
        }
