from django.contrib import admin
from .models import DatabaseConnection


@admin.register(DatabaseConnection)
class DatabaseConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'dbname', 'username', 'created_at')
    list_filter = ('host', 'port')
    search_fields = ('name', 'host', 'dbname', 'username')
    readonly_fields = ('created_at',)
