#!/bin/bash

# Migration Script for Docker Container
# Adds bar_staff_1 and bar_staff_2 columns to events table

echo "=========================================="
echo "Running Database Migration in Container"
echo "=========================================="

# Get the container name for the db service
CONTAINER_NAME=$(docker-compose ps -q db)

if [ -z "$CONTAINER_NAME" ]; then
    echo "ERROR: DB container not found. Is it running?"
    echo "Run 'docker-compose up -d' first"
    exit 1
fi

echo "Container ID: $CONTAINER_NAME"
echo ""

# Copy migration script to container
echo "Copying migration script to container..."
docker cp db-service/migrate_add_bar_staff_columns.py $CONTAINER_NAME:/app/migrate.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy migration script"
    exit 1
fi

echo "✓ Migration script copied"
echo ""

# Run migration in container
echo "Running migration..."
docker exec $CONTAINER_NAME python migrate.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Migration completed successfully!"
    echo "=========================================="
    echo ""
    echo "Restarting DB service..."
    docker-compose restart db
    echo "✓ DB service restarted"
else
    echo ""
    echo "=========================================="
    echo "✗ Migration failed!"
    echo "=========================================="
    exit 1
fi
