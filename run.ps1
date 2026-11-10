<#
.SYNOPSIS
    Convenience launcher script for VNPT OMC Management Tools Web Application.
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
    [ValidateSet("up", "down", "restart", "build", "logs", "ps", "seed", "postgres", "help")]
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
} else {
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
$PostgresCompose = "docker/docker-compose.postgres.yml"
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
    $pgState = docker ps --filter "name=^postgres$" --format "{{.Status}}"
    if (-not $pgState) {
        Write-Host "Starting independent PostgreSQL persistence stack..." -ForegroundColor Cyan
        docker compose --env-file .env -f $PostgresCompose up -d
        Write-Host "PostgreSQL started (Data persisted on host: storage/postgres_data)" -ForegroundColor Green
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
        Write-Host "Starting VNPT OMC Management Tools ($Mode mode)..." -ForegroundColor Cyan
        docker compose --env-file .env -f $CurrentCompose up -d
        
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " VNPT OMC Management Tools is running in [$Mode] mode!   " -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " Frontend (HTTPS)     : https://localhost" -ForegroundColor Yellow
        Write-Host " Frontend (HTTP Auto) : http://localhost" -ForegroundColor Yellow
        Write-Host " API Docs (Swagger)   : https://localhost/docs" -ForegroundColor Yellow
        Write-Host " Direct Backend API   : http://localhost:8000/docs" -ForegroundColor Gray
        if ($Mode -eq "dev") {
            Write-Host " Direct Vite Dev      : http://localhost:3000" -ForegroundColor Gray
        }
        Write-Host " PostgreSQL (Host)    : localhost:5432 (Data: storage/postgres_data)" -ForegroundColor Gray
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
            Write-Host "All containers stopped (Host PostgreSQL data in storage/postgres_data is preserved)." -ForegroundColor Green
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

    "help" {
        Write-Host "VNPT OMC Management Tools Launcher" -ForegroundColor Cyan
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 up [-Mode dev|release]      : Start application stack (default: dev)"
        Write-Host "  .\run.ps1 build [-Mode dev|release]   : Build images (release uses Nuitka + npm)"
        Write-Host "  .\run.ps1 down [-All]                 : Stop app stack (-All also stops postgres)"
        Write-Host "  .\run.ps1 restart [-Mode dev|release] : Restart application containers"
        Write-Host "  .\run.ps1 logs [-Mode dev|release]    : View real-time container logs"
        Write-Host "  .\run.ps1 ps                          : View container status"
        Write-Host "  .\run.ps1 seed                        : Seed default admin user"
        Write-Host "  .\run.ps1 postgres [up|down|restart]  : Manage PostgreSQL stack separately"
    }
}
