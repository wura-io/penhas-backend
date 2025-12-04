# Alembic Database Migrations

This directory contains database migration scripts managed by Alembic.

## Setup

Alembic is already configured and ready to use. The configuration:
- Uses SQLAlchemy async engine
- Automatically discovers all models from `app/models`
- Connects using settings from `app/core/config`

## Common Commands

### Create a new migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration for manual SQL
alembic revision -m "description of changes"
```

### Apply migrations
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>
```

### View migration history
```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Migration Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations** on a copy of production data
3. **Write downgrade functions** for all migrations
4. **Keep migrations small** and focused
5. **Document complex migrations** with comments

## Initial Migration

To create the initial migration from current models:

```bash
cd /Users/rchuluc/Documents/projects/wura/penhas-backend/backend_python
alembic revision --autogenerate -m "Initial migration - all models"
alembic upgrade head
```

## Compatibility with Perl API

The database schema is 100% compatible with the Perl API. All table names, column names, and data types match exactly.

When migrating from Perl:
1. The schema is already in place (managed by Sqitch in Perl)
2. No schema changes needed initially
3. Future changes can be managed via Alembic
4. Both systems can run against the same database during transition

