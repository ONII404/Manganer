<#
.SYNOPSIS
    Auditoría de seguridad básica para Manganer (PowerShell compatible)
#>

Write-Host "🔍 Iniciando auditoría de seguridad..." -ForegroundColor Cyan

$errors = @()

# 1. Verificar que .env está en .gitignore
$gitignore = Get-Content ".gitignore" -ErrorAction SilentlyContinue
if ($gitignore -notmatch "^\.env$") {
    $errors += "❌ .env no está en .gitignore"
} else {
    Write-Host "✅ .env está excluido de Git" -ForegroundColor Green
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

# 5. Verificar docker-compose.yml.example
if (!(Test-Path "docker-compose.yml.example")) {
    $errors += "❌ docker-compose.yml.example no existe"
} else {
    Write-Host "✅ docker-compose.yml.example existe" -ForegroundColor Green
    
    # Verificar que no hay rutas absolutas de Windows
    $compose = Get-Content "docker-compose.yml.example" -Raw
    if ($compose -match "[A-Z]:/[^`$]") {
        $errors += "⚠️  docker-compose.yml.example contiene rutas absolutas (usar variables)"
    } else {
        Write-Host "✅ docker-compose.yml.example usa rutas relativas/variables" -ForegroundColor Green
    }
}

# 6. Verificar que DEBUG no está hardcodeado como true en config
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