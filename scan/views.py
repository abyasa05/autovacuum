import json
import psycopg2
from django.http import JsonResponse
from django.utils import timezone
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


@require_http_methods(["POST"])
def run_vacuum(request, connection_id):
    """Run VACUUM ANALYZE on selected tables for a given connection."""
    try:
        db_conn = DatabaseConnection.objects.get(id=connection_id)
    except DatabaseConnection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Connection not found.'
        }, status=404)

    # Parse tables from request body
    try:
        data = json.loads(request.body)
        tables = data.get('tables', [])
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON payload.'
        }, status=400)

    if not tables or not isinstance(tables, list):
        return JsonResponse({
            'success': False,
            'message': 'No tables selected for vacuum.'
        }, status=400)

    try:
        conn = psycopg2.connect(
            host=db_conn.host,
            port=db_conn.port,
            dbname=db_conn.dbname,
            user=db_conn.username,
            password=db_conn.password,
            connect_timeout=5,
        )
        # VACUUM cannot run inside a transaction block
        conn.autocommit = True
        cursor = conn.cursor()

        # Validate requested tables against actual database tables
        # to prevent SQL injection via crafted table names
        cursor.execute(
            "SELECT schemaname, relname FROM pg_stat_user_tables;"
        )
        valid_tables = {
            f"{row[0]}.{row[1]}" for row in cursor.fetchall()
        }

        vacuumed = []
        skipped = []
        errors = []

        for table_name in tables:
            table_name = table_name.strip()
            if table_name not in valid_tables:
                skipped.append(table_name)
                continue

            # Split into schema and table for proper quoting
            schema, table = table_name.split('.', 1)
            qualified_name = f'"{schema}"."{table}"'

            try:
                cursor.execute(f'VACUUM ANALYZE {qualified_name};')
                vacuumed.append(table_name)
            except Exception as e:
                errors.append({
                    'table': table_name,
                    'error': str(e).strip()
                })

        cursor.close()
        conn.close()

        # Update last_vacuum timestamp on the connection
        if vacuumed:
            db_conn.last_vacuum = timezone.now()
            db_conn.save(update_fields=['last_vacuum'])

        return JsonResponse({
            'success': True,
            'vacuumed': vacuumed,
            'skipped': skipped,
            'errors': errors,
            'last_vacuum': db_conn.last_vacuum.strftime('%b %d, %Y %H:%M') if db_conn.last_vacuum else None,
            'message': f'Successfully vacuumed {len(vacuumed)} table(s).'
                       + (f' {len(skipped)} skipped.' if skipped else '')
                       + (f' {len(errors)} failed.' if errors else ''),
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
