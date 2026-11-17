#!/usr/bin/env bash
# =============================================================================
# Deployment Controller for VNPT OMC Management Tools (Server Linux)
# =============================================================================
set -e

APP_COMPOSE="docker-compose.prod.yml"
PG_COMPOSE="docker-compose.postgres.yml"
IMAGE_DIR="images"
NETWORK_NAME="omc_network"

show_help() {
    echo "=========================================================="
    echo " VNPT OMC Management Tools - Server Deployment"
    echo "=========================================================="
    echo "Usage: ./deploy.sh [load|up|down|restart|logs|ps|postgres]"
    echo ""
    echo "Commands:"
    echo "  load             : Load Docker images from images directory"
    echo "  up               : Start PostgreSQL stack & application stack"
    echo "  down [--all]     : Stop app containers (use --all to also stop PostgreSQL)"
    echo "  restart          : Restart application containers"
    echo "  logs [service]   : View container logs (e.g. ./deploy.sh logs backend)"
    echo "  ps               : Check running container status for both stacks"
    echo "  postgres [cmd]   : Manage PostgreSQL stack (up|down|restart|logs|ps)"
    echo "=========================================================="
}

ensure_network() {
    if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
        echo "Creating shared network: $NETWORK_NAME..."
        docker network create "$NETWORK_NAME" >/dev/null
    fi
}

case "$1" in
    load)
        TAR_FILE="$IMAGE_DIR/omc_mgmt_images.tar"
        GZ_FILE="$IMAGE_DIR/omc_mgmt_images.tar.gz"

        if [ ! -f "$TAR_FILE" ] && [ -f "$GZ_FILE" ]; then
            echo "Decompressing $GZ_FILE..."
            tar -xzf "$GZ_FILE" -C "$IMAGE_DIR" 2>/dev/null || true
        fi

        if [ -f "$TAR_FILE" ]; then
            echo "Loading Docker images from $TAR_FILE..."
            docker load -i "$TAR_FILE"
        elif [ -f "$GZ_FILE" ]; then
            echo "Loading Docker images from $GZ_FILE..."
            docker load < "$GZ_FILE"
        else
            echo "Error: No image archive found in $IMAGE_DIR/ (expected omc_mgmt_images.tar)"
            exit 1
        fi
        echo "All Docker images loaded successfully."
        ;;

    up)
        # Ensure .env file exists
        if [ ! -f ".env" ]; then
            if [ -f ".env.example" ]; then
                echo "Notice: .env not found, creating from .env.example..."
                cp .env.example .env
            else
                echo "Warning: Neither .env nor .env.example found. Proceeding with compose defaults."
            fi
        fi

        ensure_network

        # 1. Start independent PostgreSQL persistence stack
        if [ -f "$PG_COMPOSE" ]; then
            echo "Starting PostgreSQL Persistence Stack..."
            docker compose -f "$PG_COMPOSE" up -d
        fi

        # 2. Start Application stack
        echo "Starting OMC Management Tools (Production Stack)..."
        docker compose -f "$APP_COMPOSE" up -d

        echo ""
        echo "=========================================================="
        echo " System is UP and RUNNING!"
        echo "=========================================================="
        echo " Frontend (HTTPS) : https://localhost (or https://<server-ip>)"
        echo " Frontend (HTTP)  : http://localhost (auto redirects to HTTPS)"
        echo " API Docs         : https://localhost/docs"
        echo " PostgreSQL       : Port 5432 (Separate Stack, Volume: omc_postgres_data)"
        echo " Redis            : Port 6379 (Docker Volume: omc_redis_data)"
        echo " Backend Storage  : Docker Volume: omc_backend_data"
        echo "=========================================================="
        ;;

    down)
        echo "Stopping OMC Management Tools application containers..."
        docker compose -f "$APP_COMPOSE" down

        if [ "$2" == "--all" ] || [ "$2" == "-All" ] || [ "$2" == "all" ]; then
            if [ -f "$PG_COMPOSE" ]; then
                echo "Stopping PostgreSQL stack..."
                docker compose -f "$PG_COMPOSE" down
            fi
            echo "All application and database containers stopped. (Volumes are preserved)."
        else
            echo "Application containers stopped. PostgreSQL stack is kept running."
            echo "(Tip: Run './deploy.sh down --all' if you also want to stop PostgreSQL)."
        fi
        ;;

    restart)
        echo "Restarting application containers..."
        docker compose -f "$APP_COMPOSE" restart
        ;;

    logs)
        if [ "$2" == "postgres" ]; then
            if [ -f "$PG_COMPOSE" ]; then
                docker compose -f "$PG_COMPOSE" logs -f
            fi
        else
            docker compose -f "$APP_COMPOSE" logs -f "${@:2}"
        fi
        ;;

    ps|status)
        if [ -f "$PG_COMPOSE" ]; then
            echo "--- [PostgreSQL Stack] ---"
            docker compose -f "$PG_COMPOSE" ps
            echo ""
        fi
        echo "--- [Application Stack] ---"
        docker compose -f "$APP_COMPOSE" ps
        ;;

    postgres)
        ensure_network
        subcmd="${2:-up}"
        if [ ! -f "$PG_COMPOSE" ]; then
            echo "Error: $PG_COMPOSE not found!"
            exit 1
        fi
        case "$subcmd" in
            up)
                docker compose -f "$PG_COMPOSE" up -d
                ;;
            down)
                docker compose -f "$PG_COMPOSE" down
                ;;
            restart)
                docker compose -f "$PG_COMPOSE" restart
                ;;
            logs)
                docker compose -f "$PG_COMPOSE" logs -f
                ;;
            ps)
                docker compose -f "$PG_COMPOSE" ps
                ;;
            *)
                echo "Usage: ./deploy.sh postgres [up|down|restart|logs|ps]"
                ;;
        esac
        ;;

    *)
        show_help
        ;;
esac
