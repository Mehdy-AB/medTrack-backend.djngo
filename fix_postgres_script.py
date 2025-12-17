import os

content = """#!/bin/sh
# init-multiple-databases.sh
# Creates multiple PostgreSQL databases on container startup

set -e
set -u

create_user_and_database() {
    local database=$1
    echo "Creating database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE "$database";
        GRANT ALL PRIVILEGES ON DATABASE "$database" TO "$POSTGRES_USER";
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_user_and_database $db
    done
    echo "Multiple databases created successfully!"
fi
"""

path = r"c:\Users\mahdi\Desktop\medtrack\medTrack-backend.djngo\infrastructure\postgres\init-multiple-databases.sh"

with open(path, 'w', newline='\n') as f:
    f.write(content)

print("File written with LF line endings.")
