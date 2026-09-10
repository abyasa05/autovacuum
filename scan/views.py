import json
import psycopg2
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from connections.models import DatabaseConnection
from connections.utils import _connect_database
from history.models import VacuumHistory


@login_required
@require_http_methods(["POST"])
def check_bloat(request, connection_id):
    """Query pg_stat_user_tables for dead tuples exceeding the given threshold,
    optionally filtering by minimum table size."""
    try:
        db_conn = DatabaseConnection.objects.get(id=connection_id)
    except DatabaseConnection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Connection not found.'
        }, status=404)

    # Parse parameters from request body
    threshold = 10000
    min_table_size_kb = None
    if request.body:
        try:
            data = json.loads(request.body)
            threshold = int(data.get('threshold', 10000))
            if 'min_table_size_kb' in data and data['min_table_size_kb'] is not None:
                min_table_size_kb = int(data['min_table_size_kb'])
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    try:
        conn = _connect_database(
            db_conn.host,
            db_conn.port,
            db_conn.dbname,
            db_conn.username,
            db_conn.password,
        )
        cursor = conn.cursor()

        # Build query based on whether min_table_size_kb is set
        if min_table_size_kb is not None:
            min_size_bytes = min_table_size_kb * 1024
            cursor.execute(
                """
                SELECT schemaname, relname, n_dead_tup,
                       pg_size_pretty(pg_relation_size(relid)) AS table_size
                FROM pg_stat_user_tables
                WHERE n_dead_tup >= %s
                  AND pg_relation_size(relid) >= %s
                ORDER BY n_dead_tup DESC;
                """,
                [threshold, min_size_bytes],
            )
        else:
            cursor.execute(
                """
                SELECT schemaname, relname, n_dead_tup,
                       pg_size_pretty(pg_relation_size(relid)) AS table_size
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
                'table_size': row[3],
            }
            for row in rows
        ]
        cursor.close()
        conn.close()

        return JsonResponse({
            'success': True,
            'tables': tables,
            'threshold': threshold,
            'min_table_size_kb': min_table_size_kb,
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


@login_required
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
        conn = _connect_database(
            db_conn.host,
            db_conn.port,
            db_conn.dbname,
            db_conn.username,
            db_conn.password,
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

        # Log to VacuumHistory
        is_success = 'success'
        detail_dict = {'vacuumed': vacuumed}
        if skipped or errors:
            is_success = 'partial_success'
            detail_dict['skipped'] = skipped
            detail_dict['errors'] = errors
        detail = json.dumps(detail_dict)

        VacuumHistory.objects.create(
            connection=db_conn,
            database_name=db_conn.name,
            is_success=is_success,
            detail=detail
        )

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
        VacuumHistory.objects.create(
            connection=db_conn,
            database_name=db_conn.name,
            is_success='fail',
            detail=str(e).strip()
        )
        return JsonResponse({
            'success': False,
            'message': f'Connection failed: {str(e).strip()}'
        })
    except Exception as e:
        VacuumHistory.objects.create(
            connection=db_conn,
            database_name=db_conn.name,
            is_success='fail',
            detail=str(e).strip()
        )
        return JsonResponse({
            'success': False,
            'message': f'Unexpected error: {str(e).strip()}'
        })
