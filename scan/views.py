import json
import psycopg2
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from connections.models import DatabaseConnection


@require_http_methods(["POST"])
def check_bloat(request, connection_id):
    """Query pg_stat_user_tables for dead tuples exceeding the given threshold."""
    try:
        db_conn = DatabaseConnection.objects.get(id=connection_id)
    except DatabaseConnection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Connection not found.'
        }, status=404)

    # Parse threshold from request body, default to 10000
    threshold = 10000
    if request.body:
        try:
            data = json.loads(request.body)
            threshold = int(data.get('threshold', 10000))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    try:
        conn = psycopg2.connect(
            host=db_conn.host,
            port=db_conn.port,
            dbname=db_conn.dbname,
            user=db_conn.username,
            password=db_conn.password,
            connect_timeout=5,
        )
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT schemaname, relname, n_dead_tup
            FROM pg_stat_user_tables
            WHERE n_dead_tup >= %s
            ORDER BY n_dead_tup DESC;
            """,
            [threshold],
        )
        rows = cursor.fetchall()
        tables = [
            {
                'schema': row[0],
                'table': row[1],
                'n_dead_tup': row[2],
            }
            for row in rows
        ]
        cursor.close()
        conn.close()

        return JsonResponse({
            'success': True,
            'tables': tables,
            'threshold': threshold,
        })
    except psycopg2.OperationalError as e:
        return JsonResponse({
            'success': False,
            'message': f'Connection failed: {str(e).strip()}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Unexpected error: {str(e).strip()}'
        })
