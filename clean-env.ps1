$envPath = ".env"
$lines = Get-Content $envPath

$cleanedLines = @()
foreach ($line in $lines) {
    $trimmed = $line.Trim()
    
    # Remove BOM if present
    if ($trimmed.Length -gt 0 -and [int][char]$trimmed[0] -eq 65279) {
        $trimmed = $trimmed.Substring(1)
    }
    
    # Keep empty lines
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        $cleanedLines += ""
        continue
    }
    
    # Keep existing comments
    if ($trimmed.StartsWith('#')) {
        $cleanedLines += $trimmed
        continue
    }
    
    # Check if line contains = sign (valid env var)
    if ($trimmed -match '=') {
        # Split on first = sign
        $parts = $trimmed -split '=', 2
        # Clean the key: remove all spaces and replace with underscores
        $key = $parts[0].Trim() -replace '\s+', '_'
        $value = $parts[1]
        $cleanedLines += "$key=$value"
    } else {
        # Line doesn't contain =, it's likely a section header - comment it out
        $cleanedLines += "# $trimmed"
    }
}

# Write back to file with UTF8 no BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines($envPath, $cleanedLines, $utf8NoBom)
Write-Host "Cleaned .env file with UTF8 no BOM encoding"
