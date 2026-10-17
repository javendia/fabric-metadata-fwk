# MS Graph PowerShell Modules Docs: https://docs.microsoft.com/en-us/powershell/microsoftgraph/overview
# Installation (Run those commands - one time setup)
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#	Install-Module AzureAD -Scope CurrentUser
#   Install-Module Microsoft.Graph -Scope CurrentUser
#   Import-Module Microsoft.Graph (PowerShell 7)
#	Import-Module AzureAD
#	Get Tenant Id https://{Tenant}/sites/{Site}/_api/site/id

# Inputs

# Site ID
$siteId = Read-Host -Prompt "Please enter the site ID (GUID) of the SharePoint site"
# Azure AD application (service principal) display name
$appDisplayName = Read-Host -Prompt "Please enter display name of the Azure AD application (service principal)"
# Permission to assign
$permission = Read-Host -Prompt "Please enter the permission to assign ('read', 'write')"

# Connection
Connect-MgGraph -Scopes "Sites.Read.All","Sites.FullControl.All"
Connect-AzureAD

$sp = Get-AzureADServicePrincipal -SearchString $appDisplayName  
$appId = $sp.AppId

$site = Get-MGSite -SiteId $siteId 

# Get current permissions 
Write-Host "Before the update" -ForegroundColor Green
$permissions = Get-MgSitePermission -SiteId $siteId
$permissions | Select -ExpandProperty GrantedToIdentities | Select -ExpandProperty Application

# Add new service principal
$body = @{
  'roles' = @(
      $permission
   );
  'grantedToIdentities' = @(
      @{
        'application' = @{
          'id' = $appId
          'displayName' = $appDisplayName
        }
      }
   );
}
$bodyJson = $body | ConvertTo-Json -Depth 10 -Compress
Invoke-MgGraphRequest `
    -Method POST `
    -Uri "v1.0/sites/$SiteId/permissions" `
    -Body $bodyJson

# Get updated permissions 
Write-Host "After the update" -ForegroundColor Green
$permissions = Get-MgSitePermission -SiteId $siteId
$permissions | Select -ExpandProperty GrantedToIdentities | Select -ExpandProperty Application