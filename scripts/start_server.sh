#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure we are in the project root directory
cd "$(dirname "$0")/.."

echo "Starting Hazy Oracles User Study Server..."
echo "Mode: Semi-production (low volume)"

# Run the FastAPI server using uvicorn via uv
# Good practices for semi-production with low volume:
# - Bind to 0.0.0.0 to be accessible from outside (e.g. reverse proxy, Cloudflare tunnel)
# - Specify a set port (8000)
# - Use a small number of workers (2-4) to handle concurrent requests without using too many resources
# - Enable proxy headers to parse X-Forwarded-* headers properly when behind a proxy
uv run uvicorn hazy_oracles_user_study.server:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --proxy-headers
