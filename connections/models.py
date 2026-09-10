import base64
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

def get_fernet():
    key = settings.SECRET_KEY.encode('utf-8')
    # Fernet keys must be 32 url-safe base64-encoded bytes
    key = base64.urlsafe_b64encode(key.ljust(32, b'0')[:32])
    return Fernet(key)

class EncryptedCharField(models.CharField):
    """Custom CharField that transparently encrypts data in the DB."""
    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return get_fernet().decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            return value

    def to_python(self, value):
        if not value:
            return value
        try:
            return get_fernet().decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        try:
            get_fernet().decrypt(value.encode('utf-8'))
            return value # Already encrypted
        except Exception:
            return get_fernet().encrypt(value.encode('utf-8')).decode('utf-8')


SSL_MODE_CHOICES = [
    ('require', 'Required'),
    ('prefer', 'Preferred'),
    ('disable', 'Disabled'),
]


class DatabaseConnection(models.Model):
    """Stores PostgreSQL database connection credentials."""

    name = models.CharField(
        max_length=255,
        help_text='A friendly label for this connection'
    )
    host = models.CharField(
        max_length=255,
        help_text='Database server hostname or IP address'
    )
    port = models.IntegerField(
        default=5432,
        help_text='Database server port'
    )
    dbname = models.CharField(
        max_length=255,
        verbose_name='Database Name',
        help_text='Name of the PostgreSQL database'
    )
    username = models.CharField(
        max_length=255,
        help_text='Database username'
    )
    password = EncryptedCharField(
        max_length=255,
        blank=True,
        help_text='Database password (stored encrypted)'
    )
    ssl_mode = models.CharField(
        max_length=10,
        choices=SSL_MODE_CHOICES,
        default='prefer',
        help_text='SSL connection mode'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Updated',
        help_text='Timestamp of the last update to this connection'
    )
    last_vacuum = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Last Vacuum',
        help_text='Timestamp of the last vacuum operation'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Database Connection'
        verbose_name_plural = 'Database Connections'

    def __str__(self):
        return f'{self.name} ({self.host}:{self.port}/{self.dbname})'
