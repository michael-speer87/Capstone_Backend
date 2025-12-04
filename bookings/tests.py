from django.test import TestCase

"""
$BASE = "http://127.0.0.1:8000"



$loginBody = @{
    email    = "example2@gmail.com"
    password = "Password123!"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod `
    -Method POST `
    -Uri "$BASE/api/auth/token/" `
    -ContentType "application/json" `
    -Body $loginBody

$loginResponse
$ACCESS = $loginResponse.access



$headers = @{ Authorization = "Bearer $ACCESS" }
$profile = Invoke-RestMethod `
    -Method GET `
    -Uri "$BASE/api/profile/" `
    -Headers $headers
$profile
$vendorId = $profile.vendor.id   # if that errors, inspect $profile and adjust
$vendorId

from vendors.models import Vendor
v = Vendor.objects.get(user__email="example2@gmail.com")
print(v.id)

$vendorId = "5a1e128e-3611-4788-a4ea-8f714c2396e0"  # paste from shell


$vendorServices = Invoke-RestMethod `
    -Method GET `
    -Uri "$BASE/api/services/$vendorId/"

$vendorServices



$vendorServices | Select-Object service_id, name, duration

$serviceId = $vendorServices[0].service_id
$serviceId



$date = "2025-12-08"   # example, but any Mon–Fri in the future works

$availability = Invoke-RestMethod `
    -Method GET `
    -Uri "$BASE/api/availability/slots?vendor_id=$vendorId&service_id=$serviceId&date=$date"

$availability | Format-List *

$availability.slots




"""
