<#
.SYNOPSIS
    Convenience launcher script for VNPT OMC Report Tools Web Application.
.DESCRIPTION
    Manages Docker Compose services, logs, and database migrations.
.EXAMPLE
    .\run.ps1 up
    .\run.ps1 down
    .\run.ps1 logs
#>

param (
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "restart", "build", "logs", "ps", "seed", "help")]
    [string]$Action = "up"
)

$ComposeFile = "docker/docker-compose.yml"

switch ($Action) {
    "up" {
        Write-Host "Starting VNPT OMC Report Tools stack..." -ForegroundColor Cyan
        docker compose -f $ComposeFile up -d
        Write-Host "Services started!" -ForegroundColor Green
        Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
        Write-Host "Backend Docs: http://localhost:8000/docs" -ForegroundColor Yellow
    }
    "build" {
        Write-Host "Building and starting all containers..." -ForegroundColor Cyan
        docker compose -f $ComposeFile up --build -d
    }
    "down" {
        Write-Host "Stopping all containers..." -ForegroundColor Yellow
        docker compose -f $ComposeFile down
    }
    "restart" {
        Write-Host "Restarting containers..." -ForegroundColor Cyan
        docker compose -f $ComposeFile restart
    }
    "logs" {
        docker compose -f $ComposeFile logs -f
    }
    "ps" {
        docker compose -f $ComposeFile ps
    }
    "seed" {
        Write-Host "Seeding initial admin user..." -ForegroundColor Cyan
        docker compose -f $ComposeFile exec backend python -m app.core.seed
    }
    "help" {
        Write-Host "Usage: .\run.ps1 [up | down | restart | build | logs | ps | seed]" -ForegroundColor Yellow
    }
}

