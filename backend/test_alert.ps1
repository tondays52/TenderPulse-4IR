<#
    ==========================================================================
    Test Alert Script - Verify WhatsApp, SMS & Telegram Dispatch
    ==========================================================================
#>

. "$PSScriptRoot\dispatcher.ps1"

Write-Host "Triggering Test Alert Dispatch..." -ForegroundColor Cyan

$testTender = [PSCustomObject]@{
    id = "989901"
    tenderId = "989901"
    refNo = "RHD/DHK/2026/TEST-01"
    title = "Test Bridge Construction & Pre-Stressed Girder Fabrication Project"
    agency = "Roads and Highways Department (RHD)"
    district = "Dhaka"
    division = "Dhaka"
    estimatedCost = 450000000
    tenderSecurity = 11250000
    stdType = "e-PW3"
    closingDate = "2026-10-15 13:00"
}

Send-TenderAlert -Tender $testTender

Write-Host "`nTest dispatch cycle completed. Check terminal output above." -ForegroundColor Green
