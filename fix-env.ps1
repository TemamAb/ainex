# Ainex .env Configuration Fixer
# This script adds missing NEXT_PUBLIC_ variables based on existing backend variables

$envPath = ".env"

# Read current .env content
$content = Get-Content $envPath -Raw -Encoding UTF8

Write-Host "Fixing .env configuration..." -ForegroundColor Cyan
Write-Host ""

# Parse existing variables into hashtable
$vars = @{}
Get-Content $envPath | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        $vars[$key] = $value
    }
}

# Track what we're adding
$additions = @()

# Fix 1: Add NEXT_PUBLIC_GEMINI_API_KEY if GEMINI_API_KEY exists
if ($vars.ContainsKey('GEMINI_API_KEY') -and -not $vars.ContainsKey('NEXT_PUBLIC_GEMINI_API_KEY')) {
    $content += "`nNEXT_PUBLIC_GEMINI_API_KEY=$($vars['GEMINI_API_KEY'])"
    $additions += "NEXT_PUBLIC_GEMINI_API_KEY (from GEMINI_API_KEY)"
    Write-Host "Added: NEXT_PUBLIC_GEMINI_API_KEY" -ForegroundColor Green
}

# Fix 2: Add NEXT_PUBLIC_ETH_RPC_URL from ETH_RPC_URL
if ($vars.ContainsKey('ETH_RPC_URL') -and -not $vars.ContainsKey('NEXT_PUBLIC_ETH_RPC_URL')) {
    $content += "`nNEXT_PUBLIC_ETH_RPC_URL=$($vars['ETH_RPC_URL'])"
    $additions += "NEXT_PUBLIC_ETH_RPC_URL (from ETH_RPC_URL)"
    Write-Host "Added: NEXT_PUBLIC_ETH_RPC_URL" -ForegroundColor Green
}

# Fix 3: Add NEXT_PUBLIC_ARBITRUM_RPC_URL 
if (-not $vars.ContainsKey('NEXT_PUBLIC_ARBITRUM_RPC_URL')) {
    $arbUrl = if ($vars.ContainsKey('ARBITRUM_RPC_URL')) { $vars['ARBITRUM_RPC_URL'] } else { 'https://arb1.arbitrum.io/rpc' }
    $content += "`nNEXT_PUBLIC_ARBITRUM_RPC_URL=$arbUrl"
    $additions += "NEXT_PUBLIC_ARBITRUM_RPC_URL"
    Write-Host "Added: NEXT_PUBLIC_ARBITRUM_RPC_URL" -ForegroundColor Green
}

# Fix 4: Add NEXT_PUBLIC_BASE_RPC_URL
if (-not $vars.ContainsKey('NEXT_PUBLIC_BASE_RPC_URL')) {
    $baseUrl = if ($vars.ContainsKey('BASE_RPC_URL')) { $vars['BASE_RPC_URL'] } else { 'https://mainnet.base.org' }
    $content += "`nNEXT_PUBLIC_BASE_RPC_URL=$baseUrl"
    $additions += "NEXT_PUBLIC_BASE_RPC_URL"
    Write-Host "Added: NEXT_PUBLIC_BASE_RPC_URL" -ForegroundColor Green
}

# Fix 5: Add WebSocket URLs (default to HTTP URLs converted to WSS)
if (-not $vars.ContainsKey('NEXT_PUBLIC_ETH_WS_URL')) {
    $content += "`nNEXT_PUBLIC_ETH_WS_URL=wss://eth.llamarpc.com"
    $additions += "NEXT_PUBLIC_ETH_WS_URL (default)"
    Write-Host "Added: NEXT_PUBLIC_ETH_WS_URL" -ForegroundColor Green
}

if (-not $vars.ContainsKey('NEXT_PUBLIC_ARBITRUM_WS_URL')) {
    $content += "`nNEXT_PUBLIC_ARBITRUM_WS_URL=wss://arb1.arbitrum.io/rpc"
    $additions += "NEXT_PUBLIC_ARBITRUM_WS_URL (default)"
    Write-Host "Added: NEXT_PUBLIC_ARBITRUM_WS_URL" -ForegroundColor Green
}

if (-not $vars.ContainsKey('NEXT_PUBLIC_BASE_WS_URL')) {
    $content += "`nNEXT_PUBLIC_BASE_WS_URL=wss://mainnet.base.org"
    $additions += "NEXT_PUBLIC_BASE_WS_URL (default)"
    Write-Host "Added: NEXT_PUBLIC_BASE_WS_URL" -ForegroundColor Green
}

# Fix 6: Add ALCHEMY_MAINNET_URL from ETH_RPC_URL if missing
if (-not $vars.ContainsKey('ALCHEMY_MAINNET_URL') -and $vars.ContainsKey('ETH_RPC_URL')) {
    $content += "`nALCHEMY_MAINNET_URL=$($vars['ETH_RPC_URL'])"
    $additions += "ALCHEMY_MAINNET_URL (using ETH_RPC_URL)"
    Write-Host "Added: ALCHEMY_MAINNET_URL" -ForegroundColor Green
}

# Fix 7: Add BASESCAN_API_KEY with placeholder if missing
if (-not $vars.ContainsKey('BASESCAN_API_KEY')) {
    $content += "`nBASESCAN_API_KEY=YourApiKeyToken"
    $additions += "BASESCAN_API_KEY (placeholder)"
    Write-Host "WARNING: Added BASESCAN_API_KEY (placeholder)" -ForegroundColor Yellow
}

# Write updated content back
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($envPath, $content, $utf8NoBom)

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "DONE - Configuration Fixed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Changes Made:" -ForegroundColor White
$additions | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
Write-Host ""
Write-Host "Next: Run validation with 'node validate-env.js'" -ForegroundColor Cyan
Write-Host ""
