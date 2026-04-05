$ErrorActionPreference = "Stop"

Write-Host "Rebuilding API container..."
docker-compose restart api
Start-Sleep -Seconds 10
Write-Host "API container restarted."

Write-Host "1. Logging in as super admin..."
$adminLogin = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body "username=admin@chatsmart.ai&password=AdminUser123!" -ContentType "application/x-www-form-urlencoded"
$adminToken = $adminLogin.access_token

Write-Host "2. Creating new Business via Admin..."
$bizBody = @{
    name = "Test Merchant Shop"
    owner_email = "merchant@test.com"
    owner_password = "SecurePass123!"
} | ConvertTo-Json
$bizRes = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/businesses" -Method Post -Body $bizBody -ContentType "application/json" -Headers @{ Authorization = "Bearer $adminToken" }
Write-Host "Business created: $($bizRes.business_id)"

Write-Host "3. Logging in as Merchant..."
$merchantLogin = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body "username=merchant@test.com&password=SecurePass123!" -ContentType "application/x-www-form-urlencoded"
$merchantToken = $merchantLogin.access_token

Write-Host "4. Creating a Product..."
$productBody = @{
    name = "Awesome Widget"
    description = "The best widget ever"
    price = 19.99
    is_active = $true
} | ConvertTo-Json
$prodRes = Invoke-RestMethod -Uri "http://localhost:8000/api/merchant/products" -Method Post -Body $productBody -ContentType "application/json" -Headers @{ Authorization = "Bearer $merchantToken" }
Write-Host "Product Created: $($prodRes | ConvertTo-Json -Depth 5 -Compress)"

Write-Host "5. Getting Products..."
$prodsRes = Invoke-RestMethod -Uri "http://localhost:8000/api/merchant/products" -Method Get -Headers @{ Authorization = "Bearer $merchantToken" }
Write-Host "Returned Products: $($prodsRes.data.Count)"

Write-Host "6. Simulating a Customer Chat Message..."
$chatBody = @{
    customer_platform = "whatsapp"
    external_id = "+1234567890"
    content = "Hello, I want to order a widget"
} | ConvertTo-Json
$chatRes = Invoke-RestMethod -Uri "http://localhost:8000/api/chat/message" -Method Post -Body $chatBody -ContentType "application/json" -Headers @{ Authorization = "Bearer $merchantToken" }
Write-Host "Message Inserted! CONV_ID: $($chatRes.conversation_id), MSG_ID: $($chatRes.message_id)"

Write-Host "7. Checking Orders System..."
$ordersRes = Invoke-RestMethod -Uri "http://localhost:8000/api/merchant/orders" -Method Get -Headers @{ Authorization = "Bearer $merchantToken" }
Write-Host "Returned Orders: $($ordersRes.data.Count) (Should be 0)"

Write-Host "DONE - ALL ENDPOINTS VALIDATED!"
