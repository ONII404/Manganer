<#
.SYNOPSIS
    Script unificado para ejecutar Manganer en modo desarrollo o producción.

.DESCRIPTION
    - dev:   Levanta backend + frontend con hot-reload (2 puertos: 3000 + 8000)
    - prod:  Build del frontend + sirve todo desde FastAPI (1 puerto: 8000)
    - build: Solo compila el frontend a app/static/ (sin levantar servicios)

.USAGE
    .\run.ps1 -Mode dev    # Desarrollo con hot-reload
    .\run.ps1 -Mode prod   # Producción con build integrado
    .\run.ps1 -Mode build  # Solo build del frontend
    .\run.ps1 -Mode prod -Clean  # Producción con limpieza previa
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "prod", "build")]
    [string]$Mode,

    [switch]$Clean,          # Limpiar build anterior (solo prod/build)
    [switch]$NoFrontend,     # Solo backend (útil para debug)
    [switch]$Help           # Mostrar ayuda
)

if ($Help) {
    Get-Help $PSCommandPath -Full
    exit 0
}

# =============================================================================
# 🔧 CORRECCIÓN: Detectar la raíz del proyecto
# Si el script está en /scripts/, usamos el directorio padre (..)
# =============================================================================
if ($PSScriptRoot.EndsWith("\scripts") -or $PSScriptRoot.EndsWith("/scripts")) {
    $ProjectRoot = Split-Path $PSScriptRoot -Parent
} else {
    $ProjectRoot = $PSScriptRoot
}

$FrontendDir = Join-Path $ProjectRoot "frontend"
$StaticDir = Join-Path $ProjectRoot "app" "static"
$DataDir = Join-Path $ProjectRoot "data"
$LibraryDir = Join-Path $ProjectRoot "library"

# =============================================================================
# FUNCIONES UTILITARIAS
# =============================================================================

function Write-Step {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "`n🔹 $Message" -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Warn { param([string]$Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }

function Test-Command {
    param([string]$Command)
    $cmd = Get-Command $Command -ErrorAction SilentlyContinue
    if ($cmd) { return $true }
    
    $pathEnv = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + 
               [Environment]::GetEnvironmentVariable("Path", "User")
    $extensions = @("", ".exe", ".cmd", ".bat", ".ps1")
    
    foreach ($dir in ($pathEnv -split ';')) {
        if ($dir -and (Test-Path $dir)) {
            foreach ($ext in $extensions) {
                $candidate = Join-Path $dir "$Command$ext"
                if (Test-Path $candidate) { return $true }
            }
        }
    }
    return $false
}

function Ensure-Directory {
    param([string]$Path)
    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
        Write-Step "Creado: $Path" "Gray"
    }
}

# =============================================================================
# MODO: BUILD (Solo compilar frontend)
# =============================================================================
function Invoke-Build {
    param([switch]$Clean)
    
    Write-Step "Compilando frontend para producción..."
    
    if ($Clean -and (Test-Path $StaticDir)) {
        Write-Step "Limpiando $StaticDir..." "Yellow"
        Remove-Item -Recurse -Force $StaticDir -ErrorAction SilentlyContinue
    }
    
    Ensure-Directory $StaticDir
    
    Push-Location $FrontendDir
    try {
        Write-Step "Verificando entorno Node.js..." "Gray"
        try {
            $nodeVersion = & node --version 2>&1 | Out-String
            $npmVersion = & npm --version 2>&1 | Out-String
            Write-Step "Node: $($nodeVersion.Trim()) | npm: $($npmVersion.Trim())" "Gray"
        } catch {
            Write-Error "Node.js/npm no está disponible. Descarga desde https://nodejs.org/"
            exit 1
        }
        
        Write-Step "Ejecutando: npm run build"
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Build fallido con código $LASTEXITCODE"
            exit 1
        }
        
        Write-Step "Copiando build a app/static/..."
        Copy-Item -Recurse -Force (Join-Path $FrontendDir "dist" "*") $StaticDir
        
        $fileCount = (Get-ChildItem $StaticDir -Recurse | Measure-Object).Count
        Write-Success "Build completado: $fileCount archivos en $StaticDir"
        
    } finally {
        Pop-Location
    }
}

# =============================================================================
# MODO: DEV (Desarrollo con hot-reload)
# =============================================================================
function Invoke-Dev {
    param([switch]$NoFrontend)
    
    Write-Step "Modo DESARROLLO (hot-reload)"
    
    # Configurar proxy de Vite para apuntar a localhost (si no está ya)
    $ViteConfig = Join-Path $FrontendDir "vite.config.ts"
    if (Test-Path $ViteConfig) {
        $ViteContent = Get-Content $ViteConfig -Raw
        if ($ViteContent -notmatch "target:\s*['`"]http://localhost:8000") {
            Write-Step "Ajustando proxy de Vite a localhost:8000..." "Yellow"
            $ViteContent = $ViteContent -replace "target:\s*['`"]http://[^'`"]+['`"]", "target: 'http://localhost:8000'"
            Set-Content -Path $ViteConfig -Value $ViteContent -Encoding UTF8
        }
    }
    
    Ensure-Directory $DataDir
    Ensure-Directory $LibraryDir
    
    if (!$NoFrontend) {
        Write-Step "Iniciando backend + frontend..."
        Write-Host @"

🚀 Manganer - Modo Desarrollo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Frontend: http://localhost:3000  (hot-reload activado)
🔌 Backend:  http://localhost:8000  (API + docs)
📦 Volúmenes:
   - Datos:    $DataDir
   - Biblioteca: $LibraryDir

💡 Tips:
   - Cambios en frontend: recarga automática
   - Cambios en backend: reinicia manualmente o usa --reload
   - Para producción: .\run.ps1 -Mode prod

"@ -ForegroundColor Cyan
        
        Write-Step "Iniciando backend con Docker Compose..."
        docker compose up api redis -d
        
        Write-Step "Esperando que el backend esté listo..."
        $maxAttempts = 30
        for ($i = 0; $i -lt $maxAttempts; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Success "Backend listo en http://localhost:8000"
                    break
                }
            } catch {
                Start-Sleep -Seconds 1
            }
        }
        
        Write-Step "Iniciando frontend con Vite..."
        Push-Location $FrontendDir
        try {
            npm run dev
        } finally {
            Pop-Location
        }
        
    } else {
        Write-Step "Iniciando solo backend (NoFrontend=true)..."
        docker compose up api redis -d
        Write-Host "🔌 Backend: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "📚 API Docs: http://localhost:8000/api/docs" -ForegroundColor Cyan
    }
}

# =============================================================================
# MODO: PROD (Producción con build integrado)
# =============================================================================
function Invoke-Prod {
    param([switch]$Clean)
    
    Write-Step "Modo PRODUCCIÓN (build integrado)"
    
    # 1. Build del frontend
    Invoke-Build -Clean:$Clean
    
    # 2. Asegurar directorios de datos
    Ensure-Directory $DataDir
    Ensure-Directory $LibraryDir
    
    # 3. Verificar que static/index.html existe
    $IndexFile = Join-Path $StaticDir "index.html"
    if (!(Test-Path $IndexFile)) {
        Write-Error "No se encontró $IndexFile tras el build"
        exit 1
    }
    
    # 4. Levantar stack completo
    Write-Step "Iniciando stack de producción con Docker Compose..."
    docker compose up -d
    
    # 5. Esperar startup
    Write-Step "Esperando servicios..."
    Start-Sleep -Seconds 15
    
    # 6. Verificar salud
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 10 -ErrorAction Stop
        Write-Success "API Health: $($health.status)"
        
        $index = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($index.Content -match "<div id=`"root`">") {
            Write-Success "Frontend SPA: cargado correctamente"
        } else {
            Write-Warn "Frontend: index.html podría no contener #root"
        }
    } catch {
        Write-Warn "Verificación parcial: $($_.Exception.Message)"
    }
    
    Write-Host @"

🎉 Manganer - Producción Listo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Aplicación: http://localhost:8000
📚 API Docs:   http://localhost:8000/api/docs (si DEBUG=true)
📦 Volúmenes:
   - Datos:    $DataDir
   - Biblioteca: $LibraryDir
   - Frontend: $StaticDir

💡 Comandos útiles:
   - Ver logs:     docker compose logs -f api
   - Reiniciar:    docker compose restart api
   - Detener:      docker compose down
   - Build limpio: .\run.ps1 -Mode prod -Clean

"@ -ForegroundColor Green
}

# =============================================================================
# MAIN
# =============================================================================

Write-Host @"
╔════════════════════════════════════════╗
║  📚 Manganer - Biblioteca de Manga     ║
║  Python 3.13 • FastAPI • React 18      ║
╚════════════════════════════════════════╝
"@ -ForegroundColor Cyan

switch ($Mode) {
    "build" {
        Invoke-Build -Clean:$Clean
    }
    "dev" {
        Invoke-Dev -NoFrontend:$NoFrontend
    }
    "prod" {
        Invoke-Prod -Clean:$Clean
    }
}