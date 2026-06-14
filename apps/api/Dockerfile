# Backend container image for cloud deployment of apps/api.
# Installs Python dependencies (pyproject.toml) and runs the FastAPI app
# with Uvicorn. Used by docker-compose.yml and CI build pipelines.
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

