from django.test import TestCase

# Create your tests here.
'''
$registerBody = @{
    service_id = "6e7ca54b-ae00-4062-826e-ae55b19906ad"
    price      = 40
    duration   = 30
    is_active  = $true
} | ConvertTo-Json

Invoke-RestMethod `
    -Method POST `
    -Uri "$BASE/api/services/vendor/" `
    -Headers ($AuthHeaders + @{ "Content-Type" = "application/json" }) `
    -Body $registerBody


$updateBody = @{
    price = 45
} | ConvertTo-Json

Invoke-RestMethod `
    -Method PATCH `
    -Uri "$BASE/api/services/vendor/2412d2b9-ebc3-479d-8b84-852e3244a56c/" `
    -Headers ($AuthHeaders + @{ "Content-Type" = "application/json" }) `
    -Body $updateBody
'''