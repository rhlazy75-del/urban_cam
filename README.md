# Urban Cam Dashboard

This project is an urban camera monitoring application with a PostgreSQL database, a Python backend API, and a Vite-powered frontend dashboard.

## Project structure

- `docker-compose.yml` - orchestrates the database, backend, and frontend services.
- `backend/` - Python FastAPI backend service.
- `urban_dash/` - Vue/React-like Vite frontend dashboard.
- `database/` - PostgreSQL initialization data.
- `upload_2cam/` - shared upload folder for camera content.

## Services

- `db` - PostgreSQL database running on port `5433`.
- `backend` - FastAPI server running on port `8000`.
- `frontend` - Vite development server running on port `5173`.

## Run with Docker

From the project root (`c:\GEO\urban_cam`):

```bash
# Build images and start all services
docker compose up --build
```

If your Docker installation still uses the legacy command:

```bash
docker-compose up --build
```

## Accessing the app

- Frontend dashboard: `http://localhost:5173`
- Backend API: `http://localhost:8000`

## Notes

- The backend is configured to use the `Project_499` PostgreSQL database.
- Postgres data is persisted in the `db_data` Docker volume.
- The backend mounts the local `upload_2cam/` folder for file uploads.
