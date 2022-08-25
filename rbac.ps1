# This was for testing the Microsoft pre-built RBAC system with managed identities
# Requires azure CLI tool

$resouceGroupName = 'ft-interns'
$accountName = 'ncydsqlcosmos'
$subscription = 'CNS PROD C BA ENG 1 inside' # or subscription id: 295da806-856c-40c0-ba47-d301d02f4582
$principalId = '76ef785e-5376-4b13-9d01-2ba156b5e99b'
$roleDefinitionId = '00000000-0000-0000-0000-000000000001'
$scope = '/dbs/user_info/colls/users'
az cosmosdb sql role assignment create --account-name $accountName --resource-group $resouceGroupName --principal-id $principalId --subscription $subscription --role-definition-id $roleDefinitionId --scope $scope
