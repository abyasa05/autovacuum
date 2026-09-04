import json
import psycopg2
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from .models import DatabaseConnection


def _test_pg_connection(host, port, dbname, user, password):
    """Utility function to test a PostgreSQL connection and return a JsonResponse."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=5,
        )
        # Fetch server version as proof of connection
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return JsonResponse({
            'success': True,
            'message': f'Connection successful! Server: {version}'
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


@ensure_csrf_cookie
def dashboard_view(request):
    """Render the single-page dashboard with all saved connections."""
    connections = DatabaseConnection.objects.all()
    connections_data = [
        {
            'id': conn.id,
            'name': conn.name,
            'host': conn.host,
            'port': conn.port,
            'dbname': conn.dbname,
            'username': conn.username,
            'created_at': conn.created_at.strftime('%b %d, %Y %H:%M'),
            'last_vacuum': conn.last_vacuum.strftime('%b %d, %Y %H:%M') if conn.last_vacuum else None,
        }
        for conn in connections
    ]
    return render(request, 'connections/dashboard.html', {
        'connections_json': json.dumps(connections_data),
    })


@require_http_methods(["POST"])
def test_connection(request):
    """Test a PostgreSQL connection without saving it."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON payload.'}, status=400)

    host = data.get('host', '').strip()
    port = data.get('port', 5432)
    dbname = data.get('dbname', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not all([host, dbname, username]):
        return JsonResponse({
            'success': False,
            'message': 'Host, database name, and username are required.'
        }, status=400)

    try:
        port = int(port)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Port must be a number.'}, status=400)

    return _test_pg_connection(host, port, dbname, username, password)


@require_http_methods(["POST"])
def test_saved_connection(request, connection_id):
    """Test an existing saved connection by its ID."""
    try:
        db_conn = DatabaseConnection.objects.get(id=connection_id)
    except DatabaseConnection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Connection not found.'
        }, status=404)

    return _test_pg_connection(
        db_conn.host,
        db_conn.port,
        db_conn.dbname,
        db_conn.username,
        db_conn.password
    )


@require_http_methods(["POST"])
def add_connection(request):
    """Validate, test, and save a new database connection."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON payload.'}, status=400)

    name = data.get('name', '').strip()
    host = data.get('host', '').strip()
    port = data.get('port', 5432)
    dbname = data.get('dbname', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not all([name, host, dbname, username]):
        return JsonResponse({
            'success': False,
            'message': 'Name, host, database name, and username are required.'
        }, status=400)

    try:
        port = int(port)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Port must be a number.'}, status=400)

    # Test the connection before saving
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=username,
            password=password,
            connect_timeout=5,
        )
        conn.close()
    except psycopg2.OperationalError as e:
        return JsonResponse({
            'success': False,
            'message': f'Connection test failed — not saved. Error: {str(e).strip()}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Unexpected error during connection test: {str(e).strip()}'
        })

    # Connection succeeded — save it
    db_conn = DatabaseConnection.objects.create(
        name=name,
        host=host,
        port=port,
        dbname=dbname,
        username=username,
        password=password,
    )

    return JsonResponse({
        'success': True,
        'message': 'Connection saved successfully!',
        'connection': {
            'id': db_conn.id,
            'name': db_conn.name,
            'host': db_conn.host,
            'port': db_conn.port,
            'dbname': db_conn.dbname,
            'username': db_conn.username,
            'created_at': db_conn.created_at.strftime('%b %d, %Y %H:%M'),
            'last_vacuum': None,
        }
    })


@require_http_methods(["DELETE"])
def delete_connection(request, connection_id):
    """Delete a database connection by ID."""
    try:
        db_conn = DatabaseConnection.objects.get(id=connection_id)
    except DatabaseConnection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Connection not found.'
        }, status=404)

    db_conn.delete()
    return JsonResponse({
        'success': True,
        'message': 'Connection deleted successfully.'
    })
