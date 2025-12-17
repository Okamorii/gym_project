#!/bin/bash
set -e

echo "Waiting for database to be ready..."

# Wait for PostgreSQL to be ready using Python with environment variable
while ! python3 -c "
import os
import psycopg
try:
    # Get DATABASE_URL from environment
    db_url = os.environ.get('DATABASE_URL', '')
    # Convert SQLAlchemy URL to psycopg format
    # postgresql+psycopg://user:pass@host:port/db -> postgresql://user:pass@host:port/db
    db_url = db_url.replace('postgresql+psycopg://', 'postgresql://')
    conn = psycopg.connect(db_url)
    conn.close()
    exit(0)
except Exception as e:
    print(f'Connection failed: {e}')
    exit(1)
" 2>&1; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready!"

# Initialize database tables if needed
echo "Initializing database tables..."
flask init-db || echo "Tables may already exist, continuing..."

# Start the application
echo "Starting Workout Tracker..."
exec "$@"
