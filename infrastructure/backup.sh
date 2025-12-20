#!/bin/bash
# infrastructure/backup.sh
#
# Script for creating and managing backups of application data and databases
# Designed for production environments with Docker, Azure, and monitoring integration
# Ensures secure backup handling with encryption and access control

# Exit on any error
set -e

# Configuration variables
# Store sensitive data in environment variables or secure vault
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="app_backup_${TIMESTAMP}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-default_key}" # Should be set in CI/CD or env
AZURE_STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-myaccount}"
AZURE_STORAGE_KEY="${AZURE_STORAGE_KEY:-mykey}" # Securely injected via CI/CD
AZURE_CONTAINER="backups"
RETENTION_DAYS=30
LOG_FILE="/var/log/backups/backup_${TIMESTAMP}.log"
DB_CONTAINER="app_db" # Docker container name for database
APP_DATA_DIR="/app/data" # Application data directory in Docker volume

# Ensure log directory exists
LOG_DIR=$(dirname "$LOG_FILE")
mkdir -p "$LOG_DIR" || {
    echo "Error: Could not create log directory $LOG_DIR"
    exit 1
}

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Function to send alerts (integrates with monitoring system)
send_alert() {
    local alert_message="$1"
    log_message "ALERT: $alert_message"
    # Example: Send alert to monitoring system (e.g., Azure Monitor, Slack webhook)
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
        curl -s -X POST "$ALERT_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"Backup Alert: $alert_message\"}" || log_message "Warning: Failed to send alert"
    fi
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR" || {
    log_message "Error: Could not create backup directory $BACKUP_DIR"
    send_alert "Failed to create backup directory $BACKUP_DIR"
    exit 1
}

# Function to backup database (assumes PostgreSQL in Docker)
backup_database() {
    log_message "Starting database backup..."
    local db_backup_file="${BACKUP_DIR}/${BACKUP_NAME}_db.sql.gz"
    
    # Dump database from Docker container
    if ! docker exec "$DB_CONTAINER" pg_dumpall -U postgres | gzip > "$db_backup_file"; then
        log_message "Error: Database backup failed"
        send_alert "Database backup failed for container $DB_CONTAINER"
        exit 1
    fi
    
    log_message "Database backup completed: $db_backup_file"
    echo "$db_backup_file"
}

# Function to backup application data
backup_app_data() {
    log_message "Starting application data backup..."
    local app_backup_file="${BACKUP_DIR}/${BACKUP_NAME}_app.tar.gz"
    
    # Archive application data directory
    if ! tar -czf "$app_backup_file" -C "$APP_DATA_DIR" .; then
        log_message "Error: Application data backup failed"
        send_alert "Application data backup failed for $APP_DATA_DIR"
        exit 1
    fi
    
    log_message "Application data backup completed: $app_backup_file"
    echo "$app_backup_file"
}

# Function to encrypt backup files
encrypt_backup() {
    local file="$1"
    local encrypted_file="${file}.enc"
    
    log_message "Encrypting backup file: $file"
    if ! openssl enc -aes-256-cbc -salt -in "$file" -out "$encrypted_file" -k "$ENCRYPTION_KEY"; then
        log_message "Error: Encryption failed for $file"
        send_alert "Encryption failed for backup file $file"
        exit 1
    fi
    
    # Remove unencrypted file securely
    shred -u "$file" || rm -f "$file"
    log_message "Encryption completed: $encrypted_file"
    echo "$encrypted_file"
}

# Function to upload backup to Azure Blob Storage
upload_to_azure() {
    local file="$1"
    local blob_name=$(basename "$file")
    
    log_message "Uploading backup to Azure Blob Storage: $blob_name"
    if ! az storage blob upload \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --account-key "$AZURE_STORAGE_KEY" \
        --container-name "$AZURE_CONTAINER" \
        --file "$file" \
        --name "$blob_name" \
        --auth-mode key; then
        log_message "Error: Upload to Azure failed for $file"
        send_alert "Failed to upload backup to Azure: $blob_name"
        exit 1
    fi
    
    log_message "Upload to Azure completed: $blob_name"
}

# Function to clean up old backups (local and Azure)
cleanup_old_backups() {
    log_message "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    # Clean local backups
    find "$BACKUP_DIR" -type f -name "*.enc" -mtime +"$RETENTION_DAYS" -exec rm -f {} \;
    log_message "Local cleanup completed"
    
    # Clean Azure backups
    old_blobs=$(az storage blob list \
        --account-name "$AZURE_STORAGE_ACCOUNT" \
        --account-key "$AZURE_STORAGE_KEY" \
        --container-name "$AZURE_CONTAINER" \
        --query "[?properties.creationTime < '$(date -d "-$RETENTION_DAYS days" +%Y-%m-%dT%H:%M:%SZ)'].name" \
        --auth-mode key \
        --output tsv)
    
    for blob in $old_blobs; do
        az storage blob delete \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --account-key "$AZURE_STORAGE_KEY" \
            --container-name "$AZURE_CONTAINER" \
            --name "$blob" \
            --auth-mode key || log_message "Warning: Failed to delete Azure blob $blob"
    done
    
    log_message "Azure cleanup completed"
}

# Main backup process
main() {
    log_message "Starting backup process..."
    
    # Perform backups
    db_backup=$(backup_database)
    app_backup=$(backup_app_data)
    
    # Encrypt backups
    db_encrypted=$(encrypt_backup "$db_backup")
    app_encrypted=$(encrypt_backup "$app_backup")
    
    # Upload to Azure
    upload_to_azure "$db_encrypted"
    upload_to_azure "$app_encrypted"
    
    # Clean up old backups
    cleanup_old_backups
    
    log_message "Backup process completed successfully"
    send_alert "Backup completed successfully at $TIMESTAMP"
}

# Trap errors and send alerts
trap 'log_message "Error: Backup script failed"; send_alert "Backup script failed at $TIMESTAMP"; exit 1' ERR

# Run main process
main

exit 0