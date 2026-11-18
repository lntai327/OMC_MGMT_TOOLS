<#
.SYNOPSIS
    Deployment controller for OMC Management Tools on Windows Server.
.EXAMPLE
    .\deploy.ps1 load
    .\deploy.ps1 up
    .\deploy.ps1 down
    .\deploy.ps1 down -All
    .\deploy.ps1 logs
    .\deploy.ps1 ps
    .\deploy.ps1 postgres up
#>

param (
    [Parameter(Position=0)]
    [ValidateSet("load", "up", "down", "restart", "logs", "ps", "postgres", "help")]
    [string]$Action = "up",

    [Parameter(Position=1)]
    [string]$Param2 = "",

    [Parameter()]
    [string]$SubAction = "",

    [switch]$All
)

$ComposeFile = "docker-compose.prod.yml"
$PostgresCompose = "docker-compose.postgres.prod.yml"
$ImageDir = "images"
$NetworkName = "omc_network"

function Ensure-DockerNetwork {
    $existing = docker network ls --filter "name=^${NetworkName}$" --format "{{.Name}}"
    if (-not $existing) {
        Write-Host "Creating shared docker network: $NetworkName..." -ForegroundColor Cyan
        docker network create $NetworkName | Out-Null
    }
}

switch ($Action) {
    "load" {
        $tarFile = "$ImageDir\omc_mgmt_images.tar"
        $tarGzFile = "$ImageDir\omc_mgmt_images.tar.gz"

        # If .tar doesn't exist but .tar.gz exists, extract .tar first
        if (-not (Test-Path $tarFile) -and (Test-Path $tarGzFile)) {
            Write-Host "Decompressing $tarGzFile with tar.exe..." -ForegroundColor Cyan
            tar -xzf $tarGzFile -C $ImageDir
        }

        if (Test-Path $tarFile) {
            Write-Host "Loading Docker images from $tarFile..." -ForegroundColor Cyan
            docker load -i $tarFile
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to load Docker images from $tarFile!"
                exit $LASTEXITCODE
            }
            Write-Host "Docker images loaded successfully." -ForegroundColor Green
        } elseif (Test-Path $tarGzFile) {
            Write-Host "Loading Docker images from $tarGzFile..." -ForegroundColor Cyan
            docker load -i $tarGzFile
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to load Docker images from $tarGzFile!"
                exit $LASTEXITCODE
            }
            Write-Host "Docker images loaded successfully." -ForegroundColor Green
        } else {
            Write-Error "No image archive found in $ImageDir (expected omc_mgmt_images.tar)"
            exit 1
        }
    }

    "up" {
        if (-not (Test-Path ".env")) {
            if (Test-Path ".env.example") {
                Write-Host "Notice: .env not found, creating from .env.example..." -ForegroundColor Yellow
                Copy-Item ".env.example" ".env"
            }
        }

        Ensure-DockerNetwork

        # 1. Start independent PostgreSQL stack
        if (Test-Path $PostgresCompose) {
            Write-Host "Starting PostgreSQL Persistence Stack..." -ForegroundColor Cyan
            docker compose -f $PostgresCompose up -d
        }

        # 2. Start Application stack
        Write-Host "Starting OMC Management Tools (Production Stack)..." -ForegroundColor Cyan
        docker compose -f $ComposeFile up -d
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to start OMC Management Tools! Please check Docker status."
            exit $LASTEXITCODE
        }

        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " System is UP and RUNNING!" -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " Frontend (HTTPS) : https://localhost (or server IP)" -ForegroundColor Yellow
        Write-Host " Frontend (HTTP)  : http://localhost" -ForegroundColor Yellow
        Write-Host " API Docs         : https://localhost/docs" -ForegroundColor Yellow
        Write-Host " PostgreSQL       : Port 5432 (Separate Stack, Volume: omc_postgres_data)" -ForegroundColor Gray
        Write-Host " Redis            : Port 6379 (Volume: omc_redis_data)" -ForegroundColor Gray
        Write-Host " Storage Volume   : omc_backend_data" -ForegroundColor Gray
        Write-Host "==========================================================" -ForegroundColor Green
    }

    "down" {
        Write-Host "Stopping OMC application containers..." -ForegroundColor Yellow
        docker compose -f $ComposeFile down

        if ($All) {
            if (Test-Path $PostgresCompose) {
                Write-Host "Stopping PostgreSQL database container..." -ForegroundColor Yellow
                docker compose -f $PostgresCompose down
            }
            Write-Host "All application and database containers stopped. (Volumes are preserved)." -ForegroundColor Green
        } else {
            Write-Host "Application containers stopped. PostgreSQL stack is kept running." -ForegroundColor Green
            Write-Host "(Tip: Run '.\deploy.ps1 down -All' if you also want to stop PostgreSQL)." -ForegroundColor Gray
        }
    }

    "restart" {
        docker compose -f $ComposeFile restart
    }

    "logs" {
        docker compose -f $ComposeFile logs -f
    }

    "ps" {
        if (Test-Path $PostgresCompose) {
            Write-Host "--- [PostgreSQL Stack] ---" -ForegroundColor Cyan
            docker compose -f $PostgresCompose ps
            Write-Host ""
        }
        Write-Host "--- [Application Stack] ---" -ForegroundColor Cyan
        docker compose -f $ComposeFile ps
    }

    "postgres" {
        if (-not $SubAction) {
            $SubAction = if ($Param2) { $Param2.ToLower() } else { "up" }
        }
        if (-not (Test-Path $PostgresCompose)) {
            Write-Error "Error: $PostgresCompose not found!"
            exit 1
        }
        Ensure-DockerNetwork
        switch ($SubAction) {
            "up" {
                docker compose -f $PostgresCompose up -d
            }
            "down" {
                docker compose -f $PostgresCompose down
            }
            "restart" {
                docker compose -f $PostgresCompose restart
            }
            "logs" {
                docker compose -f $PostgresCompose logs -f
            }
            "ps" {
                docker compose -f $PostgresCompose ps
            }
            default {
                Write-Host "Usage: .\deploy.ps1 postgres [up|down|restart|logs|ps]" -ForegroundColor Yellow
            }
        }
    }

    "help" {
        Write-Host "Usage: .\deploy.ps1 [load|up|down|restart|logs|ps|postgres]" -ForegroundColor Yellow
        Write-Host "Options:"
        Write-Host "  down -All : Also stop PostgreSQL persistence stack"
    }
}
