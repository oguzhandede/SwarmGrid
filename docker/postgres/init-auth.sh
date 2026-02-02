#!/bin/bash
set -e

# Configure pg_hba.conf for scram-sha-256
cat > /var/lib/postgresql/data/pg_hba.conf << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             0.0.0.0/0               scram-sha-256
host    all             all             ::/0                    scram-sha-256
EOF

# Set password encryption to scram-sha-256
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SET password_encryption = 'scram-sha-256';
    ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
EOSQL

echo "PostgreSQL configured for SCRAM-SHA-256 authentication"
