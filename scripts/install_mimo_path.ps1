# Them D:\CURORVIP\mino-vip vao User PATH de go "mimo" / "mimo.bat" tu moi noi.
$RepoRoot = Split-Path -Parent $PSScriptRoot
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($UserPath -split ';' | Where-Object { $_ -eq $RepoRoot }) {
    Write-Host "[OK] Da co trong PATH: $RepoRoot" -ForegroundColor Green
} else {
    $NewPath = if ($UserPath) { "$UserPath;$RepoRoot" } else { $RepoRoot }
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    $env:Path = "$env:Path;$RepoRoot"
    Write-Host "[OK] Da them vao User PATH: $RepoRoot" -ForegroundColor Green
    Write-Host "    Mo terminal moi, roi chay: mimo.bat" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Lenh goi nhanh:" -ForegroundColor Cyan
Write-Host "  mimo.bat              # tu moi thu muc (sau khi mo terminal moi)"
Write-Host "  .\mimo.ps1            # PowerShell, tu thu muc mino-vip"
Write-Host "  D:\CURORVIP\mino-vip\mimo\start.bat"
