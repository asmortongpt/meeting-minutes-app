# infrastructure/azure-deploy.sh

#!/bin/bash

# Script for deploying application to Azure using Docker and GitHub Actions
# This script handles resource provisioning, container deployment, and monitoring setup

set -e  # Exit on any error
set -o pipefail  # Exit if any command in a pipeline fails

# Environment variables (safely sourced from GitHub Secrets or local env)
AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID:-}
AZURE_RESOURCE_GROUP=${AZURE_RESOURCE_GROUP:-"my-app-rg"}
AZURE_LOCATION=${AZURE_LOCATION:-"eastus"}
AZURE_APP_NAME=${AZURE_APP_NAME:-"my-app"}
AZURE_ACR_NAME=${AZURE_ACR_NAME:-"myappacr"}
DOCKER_IMAGE_TAG=${DOCKER_IMAGE_TAG:-"latest"}

# Validate required environment variables
if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo "Error: AZURE_SUBSCRIPTION_ID is not set. Please set it in GitHub Secrets or environment."
    exit 1
fi

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors and exit
handle_error() {
    log_message "Error: $1"
    exit 1
}

# Ensure Azure CLI is installed
if ! command -v az &> /dev/null; then
    handle_error "Azure CLI is not installed. Please install it first."
fi

# Login to Azure (using GitHub Actions service principal or local credentials)
log_message "Logging into Azure..."
if [ -n "$AZURE_CLIENT_ID" ] && [ -n "$AZURE_CLIENT_SECRET" ] && [ -n "$AZURE_TENANT_ID" ]; then
    az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID" || handle_error "Azure login failed."
else
    az login || handle_error "Azure login failed. Please ensure credentials are set or run 'az login' manually."
fi

# Set the active subscription
log_message "Setting Azure subscription..."
az account set --subscription "$AZURE_SUBSCRIPTION_ID" || handle_error "Failed to set Azure subscription."

# Create resource group if it doesn't exist
log_message "Checking/creating resource group $AZURE_RESOURCE_GROUP..."
if ! az group show --name "$AZURE_RESOURCE_GROUP" &> /dev/null; then
    az group create --name "$AZURE_RESOURCE_GROUP" --location "$AZURE_LOCATION" || handle_error "Failed to create resource group."
    log_message "Resource group $AZURE_RESOURCE_GROUP created."
else
    log_message "Resource group $AZURE_RESOURCE_GROUP already exists."
fi

# Create Azure Container Registry (ACR) if it doesn't exist
log_message "Checking/creating Azure Container Registry $AZURE_ACR_NAME..."
if ! az acr show --name "$AZURE_ACR_NAME" --resource-group "$AZURE_RESOURCE_GROUP" &> /dev/null; then
    az acr create --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_ACR_NAME" --sku Basic --admin-enabled true || handle_error "Failed to create ACR."
    log_message "ACR $AZURE_ACR_NAME created."
else
    log_message "ACR $AZURE_ACR_NAME already exists."
fi

# Get ACR login server and credentials
ACR_LOGIN_SERVER=$(az acr show --name "$AZURE_ACR_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query loginServer --output tsv) || handle_error "Failed to get ACR login server."
ACR_USERNAME=$(az acr credential show --name "$AZURE_ACR_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query username --output tsv) || handle_error "Failed to get ACR username."
ACR_PASSWORD=$(az acr credential show --name "$AZURE_ACR_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query passwords[0].value --output tsv) || handle_error "Failed to get ACR password."

# Login to ACR
log_message "Logging into Azure Container Registry..."
echo "$ACR_PASSWORD" | docker login "$ACR_LOGIN_SERVER" -u "$ACR_USERNAME" --password-stdin || handle_error "Failed to login to ACR."

# Build and push Docker image (assumes Dockerfile is in root directory)
log_message "Building and pushing Docker image..."
docker build -t "$ACR_LOGIN_SERVER/$AZURE_APP_NAME:$DOCKER_IMAGE_TAG" . || handle_error "Docker build failed."
docker push "$ACR_LOGIN_SERVER/$AZURE_APP_NAME:$DOCKER_IMAGE_TAG" || handle_error "Docker push failed."
log_message "Docker image pushed to $ACR_LOGIN_SERVER/$AZURE_APP_NAME:$DOCKER_IMAGE_TAG"

# Create Azure App Service Plan if it doesn't exist
log_message "Checking/creating App Service Plan..."
if ! az appservice plan show --name "$AZURE_APP_NAME-plan" --resource-group "$AZURE_RESOURCE_GROUP" &> /dev/null; then
    az appservice plan create --name "$AZURE_APP_NAME-plan" --resource-group "$AZURE_RESOURCE_GROUP" --sku S1 --is-linux || handle_error "Failed to create App Service Plan."
    log_message "App Service Plan $AZURE_APP_NAME-plan created."
else
    log_message "App Service Plan $AZURE_APP_NAME-plan already exists."
fi

# Create or update Azure Web App for containers
log_message "Checking/creating Azure Web App..."
if ! az webapp show --name "$AZURE_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" &> /dev/null; then
    az webapp create --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_APP_NAME" --plan "$AZURE_APP_NAME-plan" --deployment-container-image-name "$ACR_LOGIN_SERVER/$AZURE_APP_NAME:$DOCKER_IMAGE_TAG" || handle_error "Failed to create Web App."
    log_message "Web App $AZURE_APP_NAME created."
else
    az webapp config container set --name "$AZURE_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --docker-custom-image "$ACR_LOGIN_SERVER/$AZURE_APP_NAME:$DOCKER_IMAGE_TAG" || handle_error "Failed to update Web App container image."
    log_message "Web App $AZURE_APP_NAME updated with new image."
fi

# Configure Web App to use ACR credentials
log_message "Configuring Web App with ACR credentials..."
az webapp config appsettings set --name "$AZURE_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=TRUE DOCKER_REGISTRY_SERVER_URL="https://$ACR_LOGIN_SERVER" DOCKER_REGISTRY_SERVER_USERNAME="$ACR_USERNAME" DOCKER_REGISTRY_SERVER_PASSWORD="$ACR_PASSWORD" || handle_error "Failed to configure Web App settings."

# Restart Web App to apply changes
log_message "Restarting Web App..."
az webapp restart --name "$AZURE_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" || handle_error "Failed to restart Web App."

# Setup monitoring with Application Insights
log_message "Setting up Application Insights..."
APP_INSIGHTS_NAME="$AZURE_APP_NAME-insights"
if ! az monitor app-insights component show --app "$APP_INSIGHTS_NAME" --resource-group "$AZURE_RESOURCE_GROUP" &> /dev/null; then
    az monitor app-insights component create --app "$APP_INSIGHTS_NAME" --location "$AZURE_LOCATION" --resource-group "$AZURE_RESOURCE_GROUP" || handle_error "Failed to create Application Insights."
    log_message "Application Insights $APP_INSIGHTS_NAME created."
else
    log_message "Application Insights $APP_INSIGHTS_NAME already exists."
fi

# Link Application Insights to Web App
APP_INSIGHTS_KEY=$(az monitor app-insights component show --app "$APP_INSIGHTS_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query instrumentationKey --output tsv) || handle_error "Failed to get Application Insights key."
az webapp config appsettings set --name "$AZURE_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --settings APPINSIGHTS_INSTRUMENTATIONKEY="$APP_INSIGHTS_KEY" || handle_error "Failed to link Application Insights to Web App."

# Setup backup (weekly backup to Azure Storage)
log_message "Setting up backups..."
STORAGE_ACCOUNT_NAME="${AZURE_APP_NAME}storage"
CONTAINER_NAME="backups"
if ! az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$AZURE_RESOURCE_GROUP" &> /dev/null; then
    az storage account create --name "$STORAGE_ACCOUNT_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --location "$AZURE_LOCATION" --sku Standard_LRS || handle_error "Failed to create storage account."
    log_message "Storage account $STORAGE_ACCOUNT_NAME created."
else
    log_message "Storage account $STORAGE_ACCOUNT_NAME already exists."
fi

# Create backup container if it doesn't exist
STORAGE_KEY=$(az storage account keys list --account-name "$STORAGE_ACCOUNT_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query "[0].value" --output tsv) || handle_error "Failed to get storage account key."
if ! az storage container show --name "$CONTAINER_NAME" --account-name "$STORAGE_ACCOUNT_NAME" --account-key "$STORAGE_KEY" &> /dev/null; then
    az storage container create --name "$CONTAINER_NAME" --account-name "$STORAGE_ACCOUNT_NAME" --account-key "$STORAGE_KEY" || handle_error "Failed to create backup container."
    log_message "Backup container $CONTAINER_NAME created."
else
    log_message "Backup container $CONTAINER_NAME already exists."
fi

# Configure Web App backup
log_message "Configuring Web App backup schedule..."
az webapp config backup create --resource-group "$AZURE_RESOURCE_GROUP" --webapp-name "$AZURE_APP_NAME" --backup-name "weekly-backup" --container-url "https://$STORAGE_ACCOUNT_NAME.blob.core.windows.net/$CONTAINER_NAME" --storage-account "$STORAGE_ACCOUNT_NAME" --frequency 7d --retain-one true || handle_error "Failed to configure backup."

# Final status check
log_message "Verifying deployment status..."
az webapp show --name "$AZURE_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query state --output tsv || handle_error "Failed to verify Web App status."
log_message "Deployment completed successfully!"
log_message "Application URL: https://$AZURE_APP_NAME.azurewebsites.net"

# Clean up sensitive data from environment
unset ACR_PASSWORD
unset STORAGE_KEY

exit 0