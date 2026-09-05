# AutoVacuum — PostgreSQL Database Cleaner

A comprehensive Django-based dashboard for managing & maintaining PostgreSQL databases. It allows you to securely save database connections, analyze table bloat, and perform `VACUUM ANALYZE` operations across multiple tables with ease.

## Features

- **Database Connections** — Add, test, edit, and safely remove PostgreSQL connections via a clean dashboard interface.
- **Secure Credentials** — Database passwords are automatically encrypted in the database using symmetric encryption (Fernet) and Django's SECRET_KEY.
- **Bloat Analysis** — Connect to your database and quickly identify tables with excessive dead tuples and large relation sizes.
- **Custom Vacuum Conditions** — Define your own thresholds for "Minimum Dead Tuples" and an optional "Minimum Table Size (KB)" to filter bloated tables.
- **One-Click Vacuuming** — Execute `VACUUM ANALYZE` on selected bloated tables to recover storage and update query planner statistics.
- **Automated History Logging** — Every vacuum operation is automatically logged into a detailed Vacuum History page, capturing successes, partial failures (e.g., skipped tables), and connection errors with easily readable formatted JSON logs.

## Tech Stack

| Layer    | Technology              |
|----------|------------------------|
| Backend  | Django 5.x             |
| Database | PostgreSQL (app metadata & history) |
| Connector| psycopg2-binary        |
| Frontend | HTML / CSS / JavaScript |

## Prerequisites

- Python 3.10+
- pip

## Quick Start

### 1. Clone repository

```bash
git clone https://github.com/abyasa05/autovacuum.git
```

### 2. Initialize container

```bash
docker compose up --build -d
```

### 3. Open your browser

Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Notes

- This application does **not** include an authentication system — it is intended for internal/development use.
- The internal PostgreSQL database only stores connection metadata and vacuum history; actual PostgreSQL operations use `psycopg2` to connect directly.
- Vacuum execution is currently ran synchronously. This might potentially create timeout issues when vacuuming very large tables (needs further testing).
