# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 pango1.0-tools libpango-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi8 libxml2 libxslt1.1 fonts-dejavu-core curl \
    && rm -rf /var/lib/apt/lists/*
# create non-root user used at runtime
RUN useradd -m appuser

# Copy requirements and install dependencies with pip
WORKDIR /app
ENV PYTHONPATH=/app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and set ownership
COPY . /app
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
