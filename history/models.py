from django.db import models
from connections.models import DatabaseConnection

class VacuumHistory(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial_success', 'Partial Success'),
        ('fail', 'Fail'),
    ]

    connection = models.ForeignKey(
        DatabaseConnection, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vacuum_histories'
    )
    # Stored so we know the name even if the connection is deleted
    database_name = models.CharField(max_length=255) 
    
    is_success = models.CharField(max_length=20, choices=STATUS_CHOICES)
    vacuum_date = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Vacuum Histories"
        ordering = ['-vacuum_date']

    def __str__(self):
        return f"{self.database_name} - {self.is_success} ({self.vacuum_date})"
