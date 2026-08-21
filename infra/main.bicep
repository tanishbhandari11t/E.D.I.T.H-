targetScope = 'resourceGroup'

@description('Base name for Jimmy resources')
param name string = 'jimmy'

@description('Azure region')
param location string = resourceGroup().location

@description('Container image (ACR loginServer/repo:tag). Empty = placeholder until first azd deploy build.')
param containerImage string = ''

@description('Azure OpenAI / Foundry endpoint host URL (e.g. https://xxx.openai.azure.com/openai/v1)')
param azureOpenAiEndpoint string

@description('Azure OpenAI deployment / model name')
param azureOpenAiDeployment string = 'gpt-5.6-sol'

@description('Dashboard listen port')
param jimmyPort int = 9119

@secure()
@description('Azure OpenAI API key')
param azureOpenAiApiKey string

@secure()
@description('HMAC secret for dashboard basic-auth sessions (32+ random bytes hex/base64)')
param basicAuthSecret string

@secure()
@description('Password for jimmy1')
param jimmy1Password string

@secure()
@description('Password for jimmy2')
param jimmy2Password string

@secure()
@description('Password for jimmy3')
param jimmy3Password string

@secure()
@description('Password for jimmy4')
param jimmy4Password string

var uniqueSuffix = uniqueString(resourceGroup().id, name)
var acrName = toLower(take(replace('${name}${uniqueSuffix}', '-', ''), 50))
var kvName = take('kv-${name}-${uniqueSuffix}', 24)
var storageName = toLower(take(replace('st${name}${uniqueSuffix}', '-', ''), 24))
var lawName = 'law-${name}-${uniqueSuffix}'
var envName = 'cae-${name}-${uniqueSuffix}'
var appName = 'ca-${name}-${uniqueSuffix}'
var shareName = 'jimmy-data'
var miName = 'mi-${name}-${uniqueSuffix}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: lawName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: miName
  location: location
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

// Allow the app MI to pull images
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, identity.id, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
  }
}

resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, identity.id, 'kvsecrets')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource secretApiKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-openai-api-key'
  properties: { value: azureOpenAiApiKey }
}

resource secretAuth 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'jimmy-basic-auth-secret'
  properties: { value: basicAuthSecret }
}

resource secretPw1 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'jimmy1-password'
  properties: { value: jimmy1Password }
}

resource secretPw2 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'jimmy2-password'
  properties: { value: jimmy2Password }
}

resource secretPw3 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'jimmy3-password'
  properties: { value: jimmy3Password }
}

resource secretPw4 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'jimmy4-password'
  properties: { value: jimmy4Password }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource share 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-05-01' = {
  parent: fileService
  name: shareName
  properties: {
    shareQuota: 100
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource storageBinding 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  parent: env
  name: 'jimmyfiles'
  properties: {
    azureFile: {
      accountName: storage.name
      accountKey: storage.listKeys().keys[0].value
      shareName: shareName
      accessMode: 'ReadWrite'
    }
  }
}

var resolvedImage = empty(containerImage) ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : containerImage

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: jimmyPort
        transport: 'auto'
        allowInsecure: false
      }
      registries: empty(containerImage) ? [] : [
        {
          server: acr.properties.loginServer
          identity: identity.id
        }
      ]
      secrets: [
        {
          name: 'azure-openai-api-key'
          keyVaultUrl: secretApiKey.properties.secretUri
          identity: identity.id
        }
        {
          name: 'jimmy-basic-auth-secret'
          keyVaultUrl: secretAuth.properties.secretUri
          identity: identity.id
        }
        {
          name: 'jimmy1-password'
          keyVaultUrl: secretPw1.properties.secretUri
          identity: identity.id
        }
        {
          name: 'jimmy2-password'
          keyVaultUrl: secretPw2.properties.secretUri
          identity: identity.id
        }
        {
          name: 'jimmy3-password'
          keyVaultUrl: secretPw3.properties.secretUri
          identity: identity.id
        }
        {
          name: 'jimmy4-password'
          keyVaultUrl: secretPw4.properties.secretUri
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'jimmy'
          image: resolvedImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            { name: 'HERMES_HOME', value: '/opt/data' }
            { name: 'HERMES_DASHBOARD', value: '1' }
            { name: 'HERMES_DASHBOARD_HOST', value: '0.0.0.0' }
            { name: 'HERMES_DASHBOARD_PORT', value: string(jimmyPort) }
            { name: 'JIMMY_SEED_PROFILES', value: '1' }
            { name: 'JIMMY_DISABLE_LOGIN_RATE_LIMIT', value: '1' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
            { name: 'AZURE_FOUNDRY_BASE_URL', value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'azure-openai-api-key' }
            { name: 'AZURE_FOUNDRY_API_KEY', secretRef: 'azure-openai-api-key' }
            { name: 'HERMES_DASHBOARD_BASIC_AUTH_SECRET', secretRef: 'jimmy-basic-auth-secret' }
            { name: 'JIMMY1_PASSWORD', secretRef: 'jimmy1-password' }
            { name: 'JIMMY2_PASSWORD', secretRef: 'jimmy2-password' }
            { name: 'JIMMY3_PASSWORD', secretRef: 'jimmy3-password' }
            { name: 'JIMMY4_PASSWORD', secretRef: 'jimmy4-password' }
          ]
          // SQLite (sessions) cannot run on Azure Files/SMB — it hangs and
          // surfaces as /api/sessions "Internal server error". Keep HERMES_HOME
          // on the container filesystem; seed recreates profiles on boot.
          // For durable storage later, use Azure Disk or an external DB — not Files.
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  dependsOn: [
    storageBinding
    acrPull
    kvSecretsUser
  ]
}

output FQDN string = app.properties.configuration.ingress.fqdn
output url string = 'https://${app.properties.configuration.ingress.fqdn}/chat'
output acrLoginServer string = acr.properties.loginServer
output keyVaultName string = keyVault.name
output resourceGroupName string = resourceGroup().name
