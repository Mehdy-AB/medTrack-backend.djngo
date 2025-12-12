"""Initial migration for offers app - sets up PostgreSQL schema."""
from django.db import migrations


def create_schema_and_enums(apps, schema_editor):
    """Create PostgreSQL schema and custom enum types."""
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    schema_editor.execute('CREATE SCHEMA IF NOT EXISTS core;')
    schema_editor.execute("""
        DO $$ BEGIN
            CREATE TYPE offer_status AS ENUM ('draft', 'published', 'closed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    schema_editor.execute("""
        DO $$ BEGIN
            CREATE TYPE application_status AS ENUM ('submitted', 'accepted', 'rejected', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


class Migration(migrations.Migration):
    """Initial migration."""
    
    initial = True
    
    dependencies = []
    
    operations = [
        migrations.RunPython(create_schema_and_enums, reverse_code=migrations.RunPython.noop),
    ]
