# MiMo CLI launcher — goi binary tu mino-vip, chay trong thu muc hien tai (cwd)
$MimoRoot = Join-Path $PSScriptRoot "mimo"
$MimoCmd = Join-Path $MimoRoot "node_modules\.bin\mimo.cmd"

if (-not (Test-Path $MimoCmd)) {
    Write-Host "[!] Chua cai MiMo CLI. Dang cai..." -ForegroundColor Yellow
    Push-Location $MimoRoot
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $MimoCmd)) {
    Write-Host "[!] Khong cai duoc MiMo CLI tai: $MimoRoot" -ForegroundColor Red
    exit 1
}

& $MimoCmd @args
exit $LASTEXITCODE
