<#
.SYNOPSIS
    Auditoría de seguridad básica para Manganer (PowerShell compatible)
#>

Write-Host "🔍 Iniciando auditoría de seguridad..." -ForegroundColor Cyan

$errors = @()

# Verificar que .env está en .gitignore
$gitignore = Get-Content ".gitignore" -Raw
if ($gitignore -match "\b\.env\b") {
    Write-Host "✅ .env está excluido de Git" -ForegroundColor Green
} else {
    Write-Host "❌ .env NO está en .gitignore" -ForegroundColor Red
}

# 2. Buscar posibles secrets hardcodeados en Python
$secretPatterns = @(
    '(api_key|apikey|secret|token|password)\s*[=:]\s*[''`"][^''`"]{10,}[''`"]',
    'https?://[^:]+:[^@]+@',
    '[''`"][a-zA-Z0-9]{32,}[''`"]'
)

Write-Host "🔎 Escaneando archivos Python..." -ForegroundColor Gray
foreach ($pattern in $secretPatterns) {
    $matches = Get-ChildItem -Path "app" -Filter "*.py" -Recurse -ErrorAction SilentlyContinue | 
               Select-String -Pattern $pattern -ErrorAction SilentlyContinue
    if ($matches) {
        $errors += "⚠️  Posible secret en: $($matches.Path):$($matches.LineNumber)"
    }
}

# 3. Buscar en frontend TypeScript
Write-Host "🔎 Escaneando archivos TypeScript..." -ForegroundColor Gray
$frontendMatches = Get-ChildItem -Path "frontend/src" -Filter "*.ts*" -Recurse -ErrorAction SilentlyContinue | 
                   Select-String -Pattern "(token|key|secret)\s*[=:]\s*[''`"][^''`"]{20,}[''`"]" -ErrorAction SilentlyContinue
if ($frontendMatches) {
    $errors += "⚠️  Posible secret en frontend: $($frontendMatches.Path)"
}

if ($errors -notmatch "Posible secret") {
    Write-Host "✅ No se detectaron secrets hardcodeados obvios" -ForegroundColor Green
}

# 4. Verificar que example.env existe
if (!(Test-Path "example.env")) {
    $errors += "❌ example.env no existe"
} else {
    Write-Host "✅ example.env existe" -ForegroundColor Green
}

# 5. Verificar que DEBUG no está hardcodeado como true en config
$configContent = Get-Content "app/config.py" -Raw -ErrorAction SilentlyContinue
if ($configContent -match "DEBUG\s*=\s*['`"]?true['`"]?") {
    $errors += "⚠️  DEBUG podría estar hardcodeado como true en config.py"
} else {
    Write-Host "✅ DEBUG parece configurado vía settings" -ForegroundColor Green
}

# Resultados
Write-Host "`n📊 Resultados:" -ForegroundColor Cyan
if ($errors.Count -eq 0) {
    Write-Host "✅ ¡Sin problemas críticos detectados!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Se detectaron $($errors.Count) problemas:" -ForegroundColor Yellow
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    exit 1
}