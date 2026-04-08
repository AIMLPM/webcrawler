#!/usr/bin/env bash
# Manage a self-hosted Firecrawl instance for benchmarking.
#
# Usage:
#   ./benchmarks/firecrawl/setup.sh start    # clone, build, start
#   ./benchmarks/firecrawl/setup.sh stop     # stop and remove containers
#   ./benchmarks/firecrawl/setup.sh status   # check if running
#   ./benchmarks/firecrawl/setup.sh logs     # tail API logs
#
# Once running, the benchmark detects it automatically via FIRECRAWL_API_URL.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FC_DIR="$SCRIPT_DIR/firecrawl-src"
FC_URL="http://localhost:3002"

# ---------------------------------------------------------------------------

start() {
    if curl -sf "$FC_URL" >/dev/null 2>&1; then
        echo "Firecrawl is already running at $FC_URL"
        return 0
    fi

    # Clone if needed
    if [[ ! -d "$FC_DIR" ]]; then
        echo "Cloning Firecrawl..."
        git clone --depth 1 https://github.com/mendableai/firecrawl.git "$FC_DIR"
    else
        echo "Firecrawl source already present at $FC_DIR"
    fi

    # Write minimal env file for self-hosted mode
    cat > "$FC_DIR/.env" <<'ENVEOF'
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false
NUM_WORKERS_PER_QUEUE=4
BULL_AUTH_KEY=benchmarkonly
ENVEOF

    echo "Building and starting Firecrawl (first time takes a few minutes)..."
    cd "$FC_DIR"
    docker compose up -d --build

    # Wait for API to be ready
    echo -n "Waiting for Firecrawl API"
    for i in $(seq 1 120); do
        if curl -sf "$FC_URL" >/dev/null 2>&1; then
            echo " ready!"
            echo ""
            echo "Firecrawl is running at $FC_URL"
            echo ""
            echo "To use in benchmarks, add to your .env:"
            echo "  FIRECRAWL_API_URL=$FC_URL"
            echo ""
            echo "Or run directly:"
            echo "  FIRECRAWL_API_URL=$FC_URL python benchmarks/benchmark_all_tools.py --tools firecrawl"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    echo " timed out."
    echo "ERROR: Firecrawl did not start within 4 minutes."
    echo "Check logs: $0 logs"
    return 1
}

stop() {
    if [[ ! -d "$FC_DIR" ]]; then
        echo "Firecrawl source not found at $FC_DIR — nothing to stop."
        return 0
    fi
    echo "Stopping Firecrawl..."
    cd "$FC_DIR"
    docker compose down
    echo "Firecrawl stopped."
}

status() {
    if curl -sf "$FC_URL" >/dev/null 2>&1; then
        echo "Firecrawl is running at $FC_URL"
    else
        echo "Firecrawl is NOT running"
        if [[ -d "$FC_DIR" ]]; then
            echo "  Source present at $FC_DIR — run '$0 start' to start it"
        else
            echo "  Run '$0 start' to clone and start it"
        fi
    fi
}

logs() {
    if [[ ! -d "$FC_DIR" ]]; then
        echo "Firecrawl source not found at $FC_DIR"
        return 1
    fi
    cd "$FC_DIR"
    docker compose logs -f api worker
}

# ---------------------------------------------------------------------------

case "${1:-}" in
    start)  start ;;
    stop)   stop ;;
    status) status ;;
    logs)   logs ;;
    *)
        echo "Usage: $0 {start|stop|status|logs}"
        exit 1
        ;;
esac
