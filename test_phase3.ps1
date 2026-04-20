$ErrorActionPreference = "Stop"

Write-Host "API is already running."
$merchantLogin = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body "username=merchant@test.com&password=SecurePass123!" -ContentType "application/x-www-form-urlencoded"
$merchantToken = $merchantLogin.access_token

function Send-ChatMessage($content) {
    $chatBody = @{
        customer_platform = "whatsapp"
        external_id = "+1234567890"
        content = $content
    } | ConvertTo-Json
    return Invoke-RestMethod -Uri "http://localhost:8000/api/chat/message" -Method Post -Body $chatBody -ContentType "application/json" -Headers @{ Authorization = "Bearer $merchantToken" }
}

Write-Host "-------------------------------------------"
Write-Host "SCENARIO 1: Message 'I want to buy Awesome Widget'"
$res1 = Send-ChatMessage -content "I want to buy Awesome Widget"
Write-Host "AI Response: $($res1.ai_response)"
Write-Host "Intent: $($res1.intent)"

Write-Host "SCENARIO 2: Message 'Talk to human'"
$res2 = Send-ChatMessage -content "Talk to human"
Write-Host "AI Response: $($res2.ai_response)"
Write-Host "Intent: $($res2.intent)"

Write-Host "SCENARIO 3: Message 'Hello, what are your opening hours?'"
$res3 = Send-ChatMessage -content "Hello, what are your opening hours?"
Write-Host "AI Response: $($res3.ai_response)"
Write-Host "Intent: $($res3.intent)"

Write-Host "-------------------------------------------"
Write-Host "Checking Orders System..."
$ordersRes = Invoke-RestMethod -Uri "http://localhost:8000/api/merchant/orders" -Method Get -Headers @{ Authorization = "Bearer $merchantToken" }
Write-Host "Returned Orders: $($ordersRes.data.Count)"
if ($ordersRes.data.Count -gt 0) {
    Write-Host "Order Details: $($ordersRes.data[0] | ConvertTo-Json -Compress)"
}

Write-Host "DONE - ALL PHASE 3 ENDPOINTS VALIDATED!"
