<#
.SYNOPSIS
    Convenience launcher script for Management Tools Web Application.
.DESCRIPTION
    Manages Docker Compose services for development and release modes, separate PostgreSQL persistence stack,
    SSL/HTTPS reverse proxy, and database migrations.
.EXAMPLE
    .\run.ps1 up -Mode dev
    .\run.ps1 up -Mode release
    .\run.ps1 build -Mode release
    .\run.ps1 down
    .\run.ps1 down -All
    .\run.ps1 postgres up
    .\run.ps1 logs
#>

param (
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "restart", "build", "logs", "ps", "seed", "postgres", "export", "help")]
    [string]$Action = "up",

    [Parameter(Position=1)]
    [string]$Param2 = "",

    [Parameter()]
    [string]$Mode = "",

    [Parameter()]
    [string]$SubAction = "",

    [switch]$All
)

# Resolve Mode vs SubAction based on Action and positional arguments
if ($Action -eq "postgres") {
    if (-not $SubAction) {
        $SubAction = if ($Param2) { $Param2.ToLower() } else { "up" }
    }
    if ($SubAction -notin @("up", "down", "restart", "logs")) {
        Write-Error "Invalid postgres subaction '$SubAction'. Expected: up, down, restart, logs"
        exit 1
    }
} elseif ($Action -notin @("export", "help")) {
    if (-not $Mode) {
        $Mode = if ($Param2) { $Param2.ToLower() } else { "dev" }
    }
    if ($Mode -notin @("dev", "release")) {
        Write-Error "Invalid mode '$Mode'. Expected: dev or release"
        exit 1
    }
}

$DevCompose = "docker/docker-compose.dev.yml"
$ReleaseCompose = "docker/docker-compose.release.yml"
$PostgresCompose = "docker/docker-compose.postgres.prod.yml"
$NetworkName = "omc_network"

function Ensure-DockerNetwork {
    $existing = docker network ls --filter "name=^${NetworkName}$" --format "{{.Name}}"
    if (-not $existing) {
        Write-Host "Creating shared docker network: $NetworkName..." -ForegroundColor Cyan
        docker network create $NetworkName | Out-Null
    }
}

function Ensure-PostgresRunning {
    Ensure-DockerNetwork
    $pgImage = docker images -q omc-postgres:latest
    if (-not $pgImage) {
        Write-Host "Building omc-postgres image..." -ForegroundColor Cyan
        docker build -f docker/postgres.Dockerfile -t omc-postgres:latest .
    }
    $pgState = docker ps --filter "name=^postgres$" --format "{{.Status}}"
    if (-not $pgState) {
        Write-Host "Starting independent PostgreSQL persistence stack..." -ForegroundColor Cyan
        docker compose --env-file .env -f $PostgresCompose up -d
        Write-Host "PostgreSQL started (Docker volume: omc_postgres_data)" -ForegroundColor Green
    }
}

function Get-ComposeFile {
    if ($Mode -eq "release") {
        return $ReleaseCompose
    }
    return $DevCompose
}

$CurrentCompose = Get-ComposeFile

switch ($Action) {
    "up" {
        Ensure-PostgresRunning
        Write-Host "Starting Management Tools ($Mode mode)..." -ForegroundColor Cyan
        docker compose --env-file .env -f $CurrentCompose up -d
        
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host "Management Tools is running in [$Mode] mode!   " -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " Frontend (HTTPS)     : https://localhost" -ForegroundColor Yellow
        Write-Host " Frontend (HTTP Auto) : http://localhost" -ForegroundColor Yellow
        Write-Host " API Docs (Swagger)   : https://localhost/docs" -ForegroundColor Yellow
        Write-Host " Direct Backend API   : http://localhost:8000/docs" -ForegroundColor Gray
        if ($Mode -eq "dev") {
            Write-Host " Direct Vite Dev      : http://localhost:3000" -ForegroundColor Gray
        }
        Write-Host " PostgreSQL (Host)    : localhost:5432 (Docker volume: omc_postgres_data)" -ForegroundColor Gray
        Write-Host "==========================================================" -ForegroundColor Green
    }

    "build" {
        Ensure-DockerNetwork
        if ($Mode -eq "release") {
            Write-Host "Building Release Stack (Frontend: npm bundle, Backend: Nuitka C-binary)..." -ForegroundColor Cyan
            
            # Optional: compile frontend locally if npm is installed on host
            $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
            if ($npmCmd) {
                Write-Host "Detected host npm, pre-building frontend bundle..." -ForegroundColor Cyan
                Push-Location "frontend"
                try {
                    npm run build
                } catch {
                    Write-Warning "Host npm run build failed or skipped, Docker multi-stage will handle it."
                } finally {
                    Pop-Location
                }
            }

            docker compose --env-file .env -f $ReleaseCompose build
            Write-Host "Release build complete! Launch with: .\run.ps1 up -Mode release" -ForegroundColor Green
        } else {
            Write-Host "Building Dev Stack (Raw scripts)..." -ForegroundColor Cyan
            docker compose --env-file .env -f $DevCompose build
            Write-Host "Dev build complete! Launch with: .\run.ps1 up -Mode dev" -ForegroundColor Green
        }
    }

    "down" {
        Write-Host "Stopping OMC application containers ($Mode mode)..." -ForegroundColor Yellow
        docker compose --env-file .env -f $CurrentCompose down
        
        if ($All) {
            Write-Host "Stopping PostgreSQL database container..." -ForegroundColor Yellow
            docker compose --env-file .env -f $PostgresCompose down
            Write-Host "All containers stopped (PostgreSQL volume omc_postgres_data is preserved)." -ForegroundColor Green
        } else {
            Write-Host "Application stopped. PostgreSQL container remains running for persistence." -ForegroundColor Gray
            Write-Host "To stop PostgreSQL as well, use: .\run.ps1 down -All" -ForegroundColor Gray
        }
    }

    "restart" {
        Write-Host "Restarting containers ($Mode mode)..." -ForegroundColor Cyan
        docker compose --env-file .env -f $CurrentCompose restart
    }

    "logs" {
        docker compose --env-file .env -f $CurrentCompose logs -f
    }

    "ps" {
        Write-Host "=== PostgreSQL Stack ===" -ForegroundColor Cyan
        docker compose --env-file .env -f $PostgresCompose ps
        Write-Host "=== Application Stack ($Mode) ===" -ForegroundColor Cyan
        docker compose --env-file .env -f $CurrentCompose ps
    }

    "seed" {
        Write-Host "Seeding initial admin user..." -ForegroundColor Cyan
        docker compose --env-file .env -f $CurrentCompose exec backend python -c "import asyncio; from app.core.seed import seed_default_admin; asyncio.run(seed_default_admin())"
    }

    "postgres" {
        switch ($SubAction) {
            "up" {
                Ensure-DockerNetwork
                Write-Host "Starting PostgreSQL stack..." -ForegroundColor Cyan
                docker compose --env-file .env -f $PostgresCompose up -d
            }
            "down" {
                Write-Host "Stopping PostgreSQL stack..." -ForegroundColor Yellow
                docker compose --env-file .env -f $PostgresCompose down
            }
            "restart" {
                docker compose --env-file .env -f $PostgresCompose restart
            }
            "logs" {
                docker compose --env-file .env -f $PostgresCompose logs -f
            }
        }
    }

    "export" {
        Ensure-DockerNetwork
        Write-Host "==========================================================" -ForegroundColor Cyan
        Write-Host " Packaging Standalone Release Bundle for Server Deployment" -ForegroundColor Cyan
        Write-Host "==========================================================" -ForegroundColor Cyan

        # 1. Build images in release mode
        Write-Host "[1/4] Building all Docker images (PostgreSQL, Redis, Nuitka C, Vite Bundle)..." -ForegroundColor Cyan
        docker build -f docker/postgres.Dockerfile -t omc-postgres:latest .
        docker build -f docker/redis.Dockerfile -t omc_mgmt_tool-redis:latest .
        
        $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
        if ($npmCmd) {
            Write-Host "Pre-building frontend bundle with host npm..." -ForegroundColor Cyan
            Push-Location "frontend"
            try { npm run build } catch { Write-Warning "Host npm run build failed, Docker multi-stage will handle it." } finally { Pop-Location }
        }
        docker compose --env-file .env -f $ReleaseCompose build

        # 2. Prepare dist package directory
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $distRoot = "dist"
        $packageDir = "$distRoot\release_bundle_$timestamp"
        $imagesDir = "$packageDir\images"
        
        New-Item -ItemType Directory -Force -Path $imagesDir | Out-Null
        
        # 3. Save docker images
        Write-Host "[2/4] Exporting Docker images via docker save (this may take a few minutes)..." -ForegroundColor Cyan
        $tarPath = "$imagesDir\omc_mgmt_images.tar"
        docker save -o $tarPath omc-postgres:latest omc_mgmt_tool-redis:latest omc_mgmt_tool-backend:release omc_mgmt_tool-frontend:release
        Write-Host "Docker images exported to $tarPath" -ForegroundColor Green

        # 4. Copy config and deploy scripts
        Write-Host "[3/4] Copying deployment configurations & scripts..." -ForegroundColor Cyan
        Copy-Item "docker\docker-compose.prod.yml" "$packageDir\docker-compose.prod.yml"
        Copy-Item "docker\docker-compose.postgres.prod.yml" "$packageDir\docker-compose.postgres.prod.yml"
        Copy-Item ".env.example" "$packageDir\.env.example"
        Copy-Item "docker\deploy.sh" "$packageDir\deploy.sh"
        Copy-Item "docker\deploy.ps1" "$packageDir\deploy.ps1"

        # 5. Create final ZIP archive of release_bundle
        Write-Host "[4/4] Creating distributable ZIP archive..." -ForegroundColor Cyan
        $zipPath = "$distRoot\omc_release_$timestamp.zip"
        Compress-Archive -Path "$packageDir\*" -DestinationPath $zipPath -Force

        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " RELEASE EXPORT COMPLETE!" -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " Package folder : $packageDir" -ForegroundColor Yellow
        Write-Host " Deployable ZIP : $zipPath" -ForegroundColor Yellow
        Write-Host ""
        Write-Host " Quick deploy instructions on Server:" -ForegroundColor Cyan
        Write-Host "  1. Copy '$zipPath' to your target server and unzip it." -ForegroundColor White
        Write-Host "  2. Run: ./deploy.sh load" -ForegroundColor White
        Write-Host "  3. Run: ./deploy.sh up" -ForegroundColor White
        Write-Host "==========================================================" -ForegroundColor Green
    }

    "help" {
        Write-Host "Management Tools Launcher" -ForegroundColor Cyan
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 up [-Mode dev|release]      : Start application stack (default: dev)"
        Write-Host "  .\run.ps1 build [-Mode dev|release]   : Build images (release uses Nuitka + npm)"
        Write-Host "  .\run.ps1 down [-All]                 : Stop app stack (-All also stops postgres)"
        Write-Host "  .\run.ps1 restart [-Mode dev|release] : Restart application containers"
        Write-Host "  .\run.ps1 logs [-Mode dev|release]    : View real-time container logs"
        Write-Host "  .\run.ps1 ps                          : View container status"
        Write-Host "  .\run.ps1 seed                        : Seed default admin user"
        Write-Host "  .\run.ps1 postgres [up|down|restart]  : Manage PostgreSQL stack separately"
        Write-Host "  .\run.ps1 export                      : Build & export standalone deployable bundle for server"
    }
}
