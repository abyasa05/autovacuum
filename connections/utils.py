import psycopg2
from django.http import JsonResponse


def _connect_database(host, port, dbname, user, password, ssl_mode='prefer'):
    """Create and return a psycopg2 connection to a PostgreSQL database."""
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        connect_timeout=5,
        sslmode=ssl_mode
    )


def _test_pg_connection(host, port, dbname, user, password, ssl_mode='prefer'):
    """Utility function to test a PostgreSQL connection and return a JsonResponse."""
    try:
        conn = _connect_database(host, port, dbname, user, password, ssl_mode)
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
