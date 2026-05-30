# Empaqueta recuperado/ como sgdeaco-decreto (modo carpeta, igual que el .exe original)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> Instalando dependencias..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

Write-Host "==> Compilando con PyInstaller..." -ForegroundColor Cyan
python -m PyInstaller sgdeaco-decreto.spec --noconfirm

$dist = Join-Path $PSScriptRoot "dist\sgdeaco-decreto"
if (-not (Test-Path $dist)) {
    throw "No se genero dist\sgdeaco-decreto"
}

Write-Host ""
Write-Host "Listo. Salida:" -ForegroundColor Green
Write-Host "  $dist\sgdeaco-decreto.exe"
Write-Host ""
Write-Host "Copia junto al .exe la carpeta files\ (config.xlsx, pendientes, plantillas, generados)."
Write-Host "Ejecuta el .exe desde esa carpeta (o abrelo ahi) para que encuentre files\."
