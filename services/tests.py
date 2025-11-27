from django.test import TestCase

# Create your tests here.
'''
# --- Setup ---
$BASE = "http://127.0.0.1:8000"

$loginBody = @{
    email    = "vendor2@gmail.com"
    password = "Password123!"
} | ConvertTo-Json

$tokenResponse = Invoke-RestMethod -Method POST -Uri "$BASE/api/auth/token/" -ContentType "application/json" -Body $loginBody
$ACCESS  = $tokenResponse.access
$AuthHeaders = @{ "Authorization" = "Bearer $ACCESS" }

# --- 1) Seed list ---
$seed = Invoke-RestMethod -Method GET -Uri "$BASE/api/services/list/"
$seed | ConvertTo-Json -Depth 5

# Manually pick a service id from $seed and set:
$SERVICE_ID = "1f116871-5074-497e-821f-9ddc73698679"

# --- 2) Register service ---
$registerBody = @{
    service_id = $SERVICE_ID
    price      = 40
    duration   = 30
    is_active  = $true
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "$BASE/api/services/vendor/" -Headers ($AuthHeaders + @{ "Content-Type" = "application/json" }) -Body $registerBody

# --- 3) List vendor services ---
Invoke-RestMethod -Method GET -Uri "$BASE/api/services/vendor/" -Headers $AuthHeaders

# --- 4) Update price (PATCH) ---
$updateBody = @{
    service_id = $SERVICE_ID
    price      = 50
} | ConvertTo-Json

Invoke-RestMethod -Method PATCH -Uri "$BASE/api/services/vendor/" -Headers ($AuthHeaders + @{ "Content-Type" = "application/json" }) -Body $updateBody
'''