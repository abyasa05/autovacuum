# AutoVacuum — PostgreSQL Connection Manager

A single-page Django dashboard for managing PostgreSQL database connections. Add, test, and remove connections through a clean web interface.

## Features

- **Add Connections** — Save PostgreSQL connection credentials via a modal form
- **Test Connections** — Verify database connectivity before saving (uses `psycopg2`)
- **View Connections** — Browse all saved connections displayed as cards
- **Delete Connections** — Remove connections with a confirmation dialog

## Tech Stack

| Layer    | Technology              |
|----------|------------------------|
| Backend  | Django 5.x             |
| Database | SQLite (app metadata)  |
| Connector| psycopg2-binary        |
| Frontend | HTML / CSS / JavaScript |

## Prerequisites

- Python 3.10+
- pip

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run database migrations

```bash
python manage.py migrate
```

### 3. Start the development server

```bash
python manage.py runserver
```

### 4. Open your browser

Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Project Structure

```
autovacuum/
├── config/                  # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── connections/             # Main application
│   ├── static/
│   │   └── connections/css/styles.css
│   ├── templates/
│   │   └── connections/dashboard.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── requirements.txt
└── README.md
```

## API Endpoints

| Method   | URL                                    | Description              |
|----------|----------------------------------------|--------------------------|
| `GET`    | `/`                                    | Dashboard page           |
| `POST`   | `/api/connections/`                   | Add a new connection     |
| `POST`   | `/api/connections/test/`              | Test connection (no save)|
| `DELETE`  | `/api/connections/<id>/delete/`       | Delete a connection      |

## Data Model

**DatabaseConnection**

| Field       | Type         | Description                     |
|-------------|--------------|----------------------------------|
| `name`      | CharField    | Friendly label for the connection|
| `host`      | CharField    | Database server hostname / IP    |
| `port`      | IntegerField | Server port (default: 5432)      |
| `dbname`    | CharField    | PostgreSQL database name         |
| `username`  | CharField    | Database username                |
| `password`  | CharField    | Database password                |
| `created_at`| DateTimeField| Auto-set on creation             |

## Notes

- This application does **not** include an authentication system — it is intended for internal/development use.
- Connection passwords are stored in plain text in the local SQLite database.
- The SQLite database (`db.sqlite3`) only stores connection metadata; actual PostgreSQL operations use `psycopg2` to connect directly.
