from django.test import TestCase

"""
AVAILABILITY TESTS
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

CART TESTS
$BASE = "http://127.0.0.1:8000"
$loginBody = @{
    email    = "example3@gmail.com"    
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

$cart = Invoke-RestMethod `
    -Method GET `
    -Uri "$BASE/api/cart/" `
    -Headers $headers

$cart

$vendorId  = "5a1e128e-3611-4788-a4ea-8f714c2396e0"  # <-- real vendor UUID
$serviceId = "6e7ca54b-ae00-4062-826e-ae55b19906ad"  # <-- real service UUID

$newCartBody = @{
    preferredDate = "2025-12-10"       # yyyy-MM-dd
    preferredTime = "14:00"            # HH:mm (serializer will output HH:mm:ss)
    service_id    = $serviceId
    vendor_id     = $vendorId
} | ConvertTo-Json

$newItem = Invoke-RestMethod `
    -Method POST `
    -Uri "$BASE/api/cart/" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $newCartBody

$newItem
$cartItemId = $newItem.id
$cartItemId

$patchBody = @{
    preferredDate = "2025-12-11"
} | ConvertTo-Json

$updatedItem = Invoke-RestMethod `
    -Method PATCH `
    -Uri "$BASE/api/cart/$cartItemId/" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $patchBody

$updatedItem

$patchBody2 = @{
    preferredDate = "2025-12-12"
    preferredTime = "15:30"
} | ConvertTo-Json

$updatedItem2 = Invoke-RestMethod `
    -Method PATCH `
    -Uri "$BASE/api/cart/$cartItemId/" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $patchBody2

$updatedItem2

Invoke-RestMethod `
    -Method DELETE `
    -Uri "$BASE/api/cart/$cartItemId/" `
    -Headers $headers


$cart = Invoke-RestMethod `
    -Method GET `
    -Uri "$BASE/api/cart/" `
    -Headers $headers

$cart | Format-Table id, preferredDate, preferredTime


BOOKING TESTS
$BASE = "http://127.0.0.1:8000"
$loginBody = @{
    email    = "example3@gmail.com"    
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

$vendorId  = "5a1e128e-3611-4788-a4ea-8f714c2396e0"  # real vendor UUID
$serviceId = "6e7ca54b-ae00-4062-826e-ae55b19906ad"  # real service UUID

$bookingBody = @{
    customer = @{
        fullname     = "Jane Doe"
        contact_info = "501-555-5555"
        email        = "jane@example.com"
        address      = "123 Main St, Little Rock, AR"
    }
    items = @(
        @{
            service_id      = $serviceId
            vendor_id       = $vendorId
            preferred_date  = "2025-12-10"  # YYYY-MM-DD
            preferred_time  = "14:00"       # HH:mm
        }
    )
} | ConvertTo-Json -Depth 5

$bookingBodyMulti = @{
    customer = @{
        fullname     = "Jane Q. Doe"
        contact_info = "5015559999"
        email        = "example3@gmail.com"
        address      = "789 South Oak Street, Little Rock, AR 72205, United States of America"
    }
    items = @(
        @{
            service_id      = $serviceId
            vendor_id       = $vendorId
            preferred_date  = "2025-12-10"
            preferred_time  = "14:00"
        },
        @{
            service_id      = $serviceId
            vendor_id       = $vendorId
            preferred_date  = "2025-12-10"
            preferred_time  = "15:30"
        }
    )
} | ConvertTo-Json -Depth 5

$booking = Invoke-RestMethod `
    -Method POST `
    -Uri "$BASE/api/bookings/" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $bookingBody

$booking

$booking = Invoke-RestMethod `
    -Method POST `
    -Uri "$BASE/api/bookings/" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $bookingBodyMulti

$booking

"""
