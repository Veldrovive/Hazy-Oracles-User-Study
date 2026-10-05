# Hazy Oracles User Study

This repository contains the platform for the **Hazy Oracles User Study**, a research project aimed at developing safer, more reliable large language models (LLMs) by understanding how humans navigate ambiguity through multi-turn clarifying dialogs.

## Project Intention

Current open-source language models often make early assumptions about underspecified information in requests, leading them to incorrect or harmful outcomes. To combat this, this study collects real, human-driven multi-turn clarifying dialogs. 

Participants in the study use this secure web platform to act as either a "question asker" or a "question answerer" for given multimodal contexts (text, images, audio). The collected data will serve as a robust benchmark to evaluate and train AI systems, improving their ability to safely process complex and underspecified real-world requests.

For more detailed information regarding the study design, objectives, and protocols, please refer to [protocol.md](./protocol.md).

---

## Running the Application

The platform consists of a Python FastAPI backend (managed via `uv`) and a React/Vite frontend.

### 🐳 Running via Docker (Recommended for Production/Evaluation)

The easiest way to run the entire application (frontend built and served by the backend) is using Docker Compose.

1. Ensure Docker and Docker Compose are installed.
2. In the root of the project, run:
   ```bash
   docker-compose up --build
   ```
3. The application will be accessible at `http://localhost:8088`.

The `docker-compose.yml` uses the provided `Dockerfile` which implements a multi-stage build: it compiles the React frontend first and then bundles it with the Python backend to be served by Uvicorn.

### 💻 Running for Local Development

To run the application locally for development, you will need to start both the backend and frontend servers independently.

#### 1. Backend

The backend is built with FastAPI and uses `uv` for lightning-fast dependency management.

1. Install `uv` if you haven't already.
2. Sync the dependencies:
   ```bash
   uv sync
   ```
3. Start the development server using the provided script (which runs Uvicorn):
   ```bash
   ./scripts/start_server.sh
   ```
   *Note: This script runs the server on `http://0.0.0.0:8000`. You can also run it directly with reloading via `uv run uvicorn src.hazy_oracles_user_study.server:app --reload`.*

#### 2. Frontend

The frontend is a React application powered by Vite.

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies via npm:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. The frontend will typically be accessible at `http://localhost:5173`. Any API calls to the backend should be appropriately configured or proxied by Vite to the backend's `8000` port.
