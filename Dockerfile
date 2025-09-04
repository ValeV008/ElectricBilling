# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 POETRY_VIRTUALENVS_CREATE=false
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 pango1.0-tools libpango-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi8 libxml2 libxslt1.1 fonts-dejavu-core curl \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN /root/.local/bin/poetry install --no-root --only main
COPY . /app
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD /root/.local/bin/poetry run alembic upgrade head && \
    /root/.local/bin/poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
