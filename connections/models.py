from django.db import models


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
    password = models.CharField(
        max_length=255,
        help_text='Database password'
    )
    created_at = models.DateTimeField(auto_now_add=True)
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
