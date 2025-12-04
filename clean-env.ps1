$envPath = ".env"

# Read raw bytes to detect encoding
$bytes = [System.IO.File]::ReadAllBytes($envPath)

# Check for UTF-16 LE BOM (FF FE) or BE BOM (FE FF)
if ($bytes.Length -ge 2) {
    if ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
        Write-Host "Detected UTF-16 LE BOM"
        $content = [System.Text.Encoding]::Unicode.GetString($bytes)
    } elseif ($bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) {
        Write-Host "Detected UTF-16 BE BOM"
        $content = [System.Text.Encoding]::BigEndianUnicode.GetString($bytes)
    } else {
        # Try to detect if it's UTF-16 without BOM (looking for nulls)
        $hasNulls = $false
        for ($i = 0; $i -lt [Math]::Min($bytes.Length, 100); $i++) {
            if ($bytes[$i] -eq 0) { $hasNulls = $true; break }
        }
        
        if ($hasNulls) {
            Write-Host "Detected potential UTF-16 (null bytes found)"
            $content = [System.Text.Encoding]::Unicode.GetString($bytes)
        } else {
            Write-Host "Assuming UTF-8/ASCII"
            $content = [System.Text.Encoding]::UTF8.GetString($bytes)
        }
    }
} else {
    $content = [System.Text.Encoding]::UTF8.GetString($bytes)
}

# Split into lines
$lines = $content -split "`r`n|`n|`r"

$cleanedLines = @()
foreach ($line in $lines) {
    $trimmed = $line.Trim()
    
    # Remove any remaining null bytes or BOM chars if string conversion missed them
    $trimmed = $trimmed -replace "`0", "" -replace "\uFEFF", ""
    
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
        $value = $parts[1].Trim()
        $cleanedLines += "$key=$value"
    } else {
        # Line doesn't contain =, it's likely a section header - comment it out
        $cleanedLines += "# $trimmed"
    }
}

# Write back to file with UTF8 no BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines($envPath, $cleanedLines, $utf8NoBom)
Write-Host "Cleaned .env file and enforced UTF-8 no BOM encoding"
