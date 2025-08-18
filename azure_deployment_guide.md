# Azure Deployment Guide for Email QA System

## Overview

The Email QA System now supports Azure deployments in addition to Replit. This guide explains how to configure the ScrapingBee API key and other secrets in Azure environments.

## Environment Detection

The application automatically detects the deployment environment:

- **Azure DevOps**: Detected via `BUILD_BUILDID`, `AZURE_PIPELINE`, or `SYSTEM_TEAMFOUNDATIONCOLLECTIONURI` environment variables
- **Azure App Service**: Detected via `WEBSITE_SITE_NAME` or `APPSETTING_WEBSITE_SITE_NAME`
- **Azure Functions**: Detected via `APPSETTING_WEBSITE_SITE_NAME`
- **Azure Managed Identity**: Detected via `AZURE_CLIENT_ID`
- **Replit**: Detected via `REPL_ID` or `REPLIT_ENVIRONMENT`
- **Local/Development**: Default fallback

## Azure Configuration Methods

### 1. Azure DevOps Pipeline Variables

For Azure DevOps deployments, configure the ScrapingBee API key as a pipeline variable:

```yaml
# azure-pipelines.yml
variables:
  - group: 'email-qa-secrets'  # Variable group containing SCRAPINGBEE_API_KEY
  - name: 'SCRAPINGBEE_API_KEY'
    value: '$(scrapingbee-api-key)'  # Reference to secret variable
```

**Steps to configure:**

1. Go to Azure DevOps → Library → Variable groups
2. Create a new variable group named `email-qa-secrets`
3. Add variable `SCRAPINGBEE_API_KEY` with your ScrapingBee API key
4. Mark it as secret (lock icon)
5. Reference the variable group in your pipeline

### 2. Azure App Service Application Settings

For Azure App Service deployments:

1. Go to Azure Portal → App Services → Your App
2. Navigate to Configuration → Application settings
3. Add new application setting:
   - **Name**: `SCRAPINGBEE_API_KEY`
   - **Value**: Your ScrapingBee API key
4. Click Save

### 3. Azure Key Vault Integration

For enhanced security using Azure Key Vault:

```yaml
# azure-pipelines.yml
variables:
  - group: 'keyvault-secrets'  # Variable group linked to Key Vault

steps:
- task: AzureKeyVault@2
  inputs:
    azureSubscription: 'your-service-connection'
    keyVaultName: 'your-keyvault'
    secretsFilter: 'scrapingbee-api-key'
    runAsPreJob: true
```

### 4. Environment Variables in Deployment

Set environment variables directly in your deployment configuration:

```bash
# For container deployments
export SCRAPINGBEE_API_KEY="your-api-key-here"

# For systemd services
Environment=SCRAPINGBEE_API_KEY=your-api-key-here
```

## Supported API Keys

The application supports two cloud browser automation services:

1. **ScrapingBee** (Primary)
   - Environment variable: `SCRAPINGBEE_API_KEY`
   - Sign up at: https://www.scrapingbee.com/

2. **Browserless** (Secondary)
   - Environment variable: `BROWSERLESS_API_KEY`
   - Sign up at: https://www.browserless.io/

## Verification

The application will automatically detect the environment and log the configuration:

```
INFO - Detected environment: azure
INFO - Azure environment detected - using environment variables for API keys
INFO - ScrapingBee API key found in environment variables: 28ZE...
```

## Security Best Practices

1. **Never commit API keys to source control**
2. **Use Azure Key Vault for production secrets**
3. **Restrict access to variable groups in Azure DevOps**
4. **Rotate API keys regularly**
5. **Monitor API usage and costs**

## Troubleshooting

### Common Issues

1. **API key not found**
   - Verify the environment variable name is exactly `SCRAPINGBEE_API_KEY`
   - Check that the variable is accessible in the deployment environment
   - Ensure the variable group is linked to your pipeline

2. **Permission errors**
   - Verify the service principal has access to Key Vault (if using)
   - Check variable group permissions in Azure DevOps

3. **Detection issues**
   - Manually set `AZURE_PIPELINE=true` to force Azure environment detection
   - Check logs for environment detection messages

### Debug Information

The application logs detailed information about environment detection and API key loading:

```
INFO - Detected environment: azure
INFO - Azure environment detected - using environment variables for API keys
INFO - Azure environment detected, using cloud browser availability: true
```

## Migration from Replit

If migrating from Replit to Azure:

1. Export your ScrapingBee API key from Replit Secrets
2. Configure it in Azure using one of the methods above
3. Update your deployment pipeline to include the new environment variables
4. Test the deployment to ensure cloud browser automation works

The application maintains backward compatibility with Replit deployments while adding Azure support.
