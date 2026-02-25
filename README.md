# CodeMan Community

CodeMan Community is a full-stack web application featuring a Python FastAPI backend and a Vue 3 frontend. It provides a platform for coding discussions, sharing works, and community interaction.

## Project Structure

- **codeman-backend/**: FastAPI backend service.
- **codeman-frontend/**: Vue 3 + Vite frontend application.
- **docker-compose.yml**: Orchestration for containerized deployment.
- **start_deployment.bat**: One-click start script for Windows (local development).

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (Recommended for deployment)
- OR
- **Python 3.8+** and **Node.js 14+** (For local development)

### 🐳 Deployment with Docker (Recommended)

This is the easiest way to run the application in a consistent environment.

1.  **Clone the repository** (if you haven't already).
2.  **Run with Docker Compose**:
    ```bash
    docker-compose up -d --build
    ```
3.  **Access the application**:
    - Frontend: [http://localhost:5173](http://localhost:5173)
    - Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

To stop the services:
```bash
docker-compose down
```

### 💻 Local Development (Windows)

If you prefer running directly on your machine:

1.  **Run the start script**:
    Double-click `start_deployment.bat` in the root directory.

    *Or manually:*

2.  **Backend**:
    ```bash
    cd codeman-backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
    ```

3.  **Frontend**:
    ```bash
    cd codeman-frontend
    npm install
    npm run dev
    ```

## Configuration

- **Database**: SQLite is used by default. The database file `database.db` is located in the `codeman-backend` directory.
- **Ports**:
    - Backend: 8000
    - Frontend: 5173 (Docker maps container port 80 to host 5173)

## Features

- **User Authentication**: Login/Register (integrated with Codemao).
- **Forum**: Create posts, comments, and view categories.
- **Works**: Share and view coding works.
- **Notifications**: Real-time updates on interactions.
- **API Documentation**: Auto-generated Swagger UI at `/docs`.

## License

MIT
