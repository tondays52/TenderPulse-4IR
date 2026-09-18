<#
    ==========================================================================
    TenderPulse 4IR - Real-Time Multi-Channel Alert Dispatcher
    Supports: WhatsApp (CallMeBot / Twilio), BD SMS (Greenweb), & Telegram
    ==========================================================================
#>

param(
    [string]$ConfigPath = "c:\Users\tonda\OneDrive\Desktop\tender\config\alerts_config.json"
)

function Get-AlertConfig {
    if (Test-Path $ConfigPath) {
        try {
            return Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {
            return $null
        }
    }
    return $null
}

function Send-TenderAlert {
    param(
        [Parameter(Mandatory=$true)]
        $Tender
    )

    $config = Get-AlertConfig
    if (-not $config -or -not $config.notifications.enabled) {
        return
    }

    $costCr = ($Tender.estimatedCost / 10000000).ToString("F2")
    $secLakh = ($Tender.tenderSecurity / 100000).ToString("F1")

    # Formatted Message for WhatsApp / Telegram
    $messageText = @"
🚨 *NEW e-GP TENDER NOTICE* 🚨
━━━━━━━━━━━━━━━━━━━━
📌 *ID:* #${Tender.tenderId}
🏢 *Agency:* ${Tender.agency}
📍 *District:* ${Tender.district}, ${Tender.division}
💼 *Project:* ${Tender.title}
💰 *Est. Value:* BDT $costCr Crore
🔒 *Security:* BDT $secLakh Lakh
📄 *CPTU STD:* Form ${Tender.stdType}
⏰ *Deadline:* ${Tender.closingDate}
━━━━━━━━━━━━━━━━━━━━
⚡ Auto-mined by *TenderPulse 4IR*
"@

    # Short format for SMS (under 160 characters)
    $smsText = "Tender Alert: #${Tender.tenderId} by ${Tender.agency} (${Tender.district}). Value: BDT $costCr Cr. Closes: ${Tender.closingDate}. Details on TenderPulse."

    $providers = $config.notifications.providers

    # 1. WhatsApp via CallMeBot (Free direct WhatsApp message)
    if ($providers.whatsapp_callmebot.enabled) {
        $phone = $providers.whatsapp_callmebot.phone
        $apiKey = $providers.whatsapp_callmebot.apiKey

        if ($apiKey -and $apiKey -notmatch "PASTE_" -and $phone -notmatch "XXXX") {
            try {
                $encoded = [System.Uri]::EscapeDataString($messageText)
                $url = "https://api.callmebot.com/whatsapp.php?phone=$phone&text=$encoded&apikey=$apiKey"
                $res = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
                Write-Host "[DISPATCHER SUCCESS] Real WhatsApp sent to $phone via CallMeBot!" -ForegroundColor Green
            } catch {
                Write-Host "[DISPATCHER WARNING] CallMeBot error: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "[MOCK WHATSAPP DISPATCH] Formatted alert ready for $phone (Add CallMeBot API key in config/alerts_config.json)" -ForegroundColor DarkCyan
        }
    }

    # 2. Twilio WhatsApp / SMS
    if ($providers.twilio_whatsapp_sms.enabled) {
        $sid = $providers.twilio_whatsapp_sms.accountSid
        $token = $providers.twilio_whatsapp_sms.authToken
        $fromWa = $providers.twilio_whatsapp_sms.fromWhatsApp
        $toPhone = $providers.twilio_whatsapp_sms.toPhone

        if ($sid -and $sid -notmatch "YOUR_" -and $token -notmatch "YOUR_") {
            try {
                $pair = "$sid`:$token"
                $encodedAuth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
                $headers = @{ Authorization = "Basic $encodedAuth" }

                # WhatsApp via Twilio
                $body = @{
                    From = $fromWa
                    To = "whatsapp:$toPhone"
                    Body = $messageText
                }
                $twilioUrl = "https://api.twilio.com/2010-04-01/Accounts/$sid/Messages.json"
                $res = Invoke-RestMethod -Uri $twilioUrl -Method Post -Headers $headers -Body $body
                Write-Host "[DISPATCHER SUCCESS] Twilio WhatsApp delivered to $toPhone (SID: $($res.sid))" -ForegroundColor Green
            } catch {
                Write-Host "[DISPATCHER WARNING] Twilio error: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }

    # 3. Bangladesh Local SMS (Greenweb)
    if ($providers.greenweb_bd_sms.enabled) {
        $token = $providers.greenweb_bd_sms.token
        $to = $providers.greenweb_bd_sms.toPhone
        if ($token -and $token -notmatch "YOUR_") {
            try {
                $body = @{
                    token = $token
                    to = $to
                    message = $smsText
                }
                $res = Invoke-RestMethod -Uri "https://api.greenweb.com.bd/api.php" -Method Post -Body $body
                Write-Host "[DISPATCHER SUCCESS] Bangladesh SMS sent to $to via Greenweb" -ForegroundColor Green
            } catch {
                Write-Host "[DISPATCHER WARNING] Greenweb SMS error: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }

    # 4. Telegram Instant Push
    if ($providers.telegram_instant_push.enabled) {
        $botToken = $providers.telegram_instant_push.botToken
        $chatId = $providers.telegram_instant_push.chatId
        if ($botToken -and $botToken -notmatch "YOUR_") {
            try {
                $tgUrl = "https://api.telegram.org/bot$botToken/sendMessage"
                $tgBody = @{
                    chat_id = $chatId
                    text = $messageText
                    parse_mode = "Markdown"
                }
                $res = Invoke-RestMethod -Uri $tgUrl -Method Post -Body ($tgBody | ConvertTo-Json) -ContentType "application/json"
                Write-Host "[DISPATCHER SUCCESS] Telegram push alert sent to Chat $chatId" -ForegroundColor Green
            } catch {
                Write-Host "[DISPATCHER WARNING] Telegram error: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
}
