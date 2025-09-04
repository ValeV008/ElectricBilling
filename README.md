# Electricity Billing System (FastAPI + Jinja2 + HTMX + SQLAlchemy + Alembic + WeasyPrint)

Minimal admin-style app for importing CSVs with dynamic electricity pricing, computing totals, and generating PDF invoices.

---

## Tech Overview

This project demonstrates:

- Importing **CSV** files with consumption & dynamic pricing data
- Storing data in a **PostgreSQL** database
- Generating invoices (HTML with Jinja2 → PDF via WeasyPrint)
- A lightweight **web interface** built with **FastAPI + Jinja2 + HTMX**
- Database schema management with **Alembic**
- Containerized deployment using **Docker & docker-compose**

## Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
- **Templating**: Jinja2 + HTMX (dynamic partial updates)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Migrations**: Alembic
- **PDF Rendering**: WeasyPrint
- **Frontend styling**: Tailwind CSS
- **Containerization**: Docker & docker-compose
- **Dependency management**: Poetry

## Requirements

- Python **3.12**
- **Poetry** (dependency & venv manager)
  ```
  pip install poetry
  ```

## Project Setup

- Clone and enter the repo
  ```
  git clone <your-repo-url>
  cd electric-billing
  ```
- Create local .env

  ```
  cp .env.example .env
  ```

- Install dependencies into a Poetry virtualenv
  ```
  poetry install
  ```

## Run App Locally

- Activate the Poetry shell (optional)

  ```
  poetry shell
  ```

- Apply DB migrations

  ```
  poetry run alembic upgrade head
  ```

- Start the dev server (reload)

  ```
  poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

- Access the app at http://localhost:8000

## Run App Containerized

- Build and Start Containers

  ```
  docker compose up --build
  ```

- Open webapp in browser
  ```
  http://localhost:8000
  ```

## Licence

MIT
