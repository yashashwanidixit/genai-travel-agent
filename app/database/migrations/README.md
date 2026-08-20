# Database Migrations

This directory contains schema migrations managed via Alembic or automated SQLAlchemy table initialization.

To initialize or generate a new migration:
```bash
alembic revision --autogenerate -m "initial migration"
alembic upgrade head
```
