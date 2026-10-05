# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy dependency files first for caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy the rest of the frontend source code
COPY frontend/ ./
# Build the frontend (outputs to dist/)
RUN npm run build


# Stage 2: Build the backend and prepare the final image
FROM python:3.12-slim

# Install uv for fast Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation for slightly faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy project metadata required for dependency resolution
COPY pyproject.toml uv.lock README.md ./

# Install project dependencies into a virtual environment in /app/.venv
RUN uv sync --frozen --no-install-project --no-dev

# Copy the backend source code
COPY src/ ./src/
COPY data/ ./data/

# Install the project itself
RUN uv sync --frozen --no-dev

# Copy the built frontend from Stage 1 to where the backend expects it
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose the port that Uvicorn will listen on
EXPOSE 8000

# Set PATH to use the virtual environment's executables
ENV PATH="/app/.venv/bin:$PATH"

# Set default host and port environment variables if needed
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the FastAPI app via Uvicorn
CMD ["uvicorn", "src.hazy_oracles_user_study.server:app", "--host", "0.0.0.0", "--port", "8000"]
