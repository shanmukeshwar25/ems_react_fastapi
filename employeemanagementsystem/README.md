# Tektalis EMS — Employee Management System

A full-stack Employee Management System with AI-powered chatbot (Aura), attendance tracking, leave management, timesheets, holiday calendar, and audit logging.

---

## Architecture

| Service | Stack | Default Port |
|---------|-------|-------------|
| **FastAPI Backend** | Python 3.11, FastAPI, SQLAlchemy, psycopg2 | `8000` |
| **React Frontend** | React 18, Vite, TanStack Query, Zustand | `5173` (dev) / `80` (Docker) |
| **React Native App** | Expo SDK 54, Expo Router | — (runs on device/emulator) |
| **PostgreSQL** | Postgres 15 | `5432` |

---

## Prerequisites

- **Python 3.11+** (for the backend)
- **Node.js 18+** and **npm** (for the frontend)
- **PostgreSQL 15+** running locally (or use Docker for the DB only)
- **Groq API key** — free at [console.groq.com/keys](https://console.groq.com/keys)
- **Docker & Docker Compose** *(only needed for the Docker workflow)*
- **Expo CLI** *(only needed for the mobile app)*

---

## Option A — Run with Docker Compose (recommended)

This is the easiest way to run the full stack. Docker Compose starts the database, backend, and frontend together.

### 1. Copy and configure the root `.env`

```bash
cd employeemanagementsystem

# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in at minimum:
- `DB_PASSWORD` — any password you choose
- `GROQ_API_KEY` — from [console.groq.com/keys](https://console.groq.com/keys)
- `MAIL_USERNAME` / `MAIL_PASSWORD` — Gmail + App Password (optional, for email notifications)

### 2. Start all services

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Backend API | http://localhost:8000/api |
| API Docs (Swagger) | http://localhost:8000/docs |

### 3. Stop all services

```bash
docker compose down

# To also delete the database volume (full reset):
docker compose down -v
```

---

## Option B — Run Each Service Individually (without Docker)

Use this if you want to develop and hot-reload each service separately. You need PostgreSQL installed and running on your machine first.

### Step 0 — Set up PostgreSQL

Create the database:

```sql
-- In psql or pgAdmin:
CREATE DATABASE "EMSNew";
```

The backend's SQLAlchemy will create all tables automatically on first startup.

---

### Step 1 — Run the FastAPI Backend

```bash
cd ems-backend-python

# Create a virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# Open .env and set DB_PASSWORD, GROQ_API_KEY, MAIL_PASSWORD, etc.

# Start the server
uvicorn main:app --reload --port 8000
```

The backend will be available at **http://localhost:8000**.  
Interactive API docs: **http://localhost:8000/docs**

---

### Step 2 — Run the React Frontend

Open a **new terminal**:

```bash
cd ems-frontend

# Install dependencies
npm install

# Configure environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# The default .env works out of the box for local development.
# Vite proxies /api → http://localhost:8000 automatically.

# Start the dev server
npm run dev
```

The frontend will be available at **http://localhost:5173**.

> **Note:** The frontend proxies all `/api` requests to the backend via Vite's dev proxy,
> so CORS is not an issue during local development.

---

### Step 3 — Run the Mobile App (Expo / React Native) — optional

Open a **new terminal**:

```bash
cd ems-frontendnative

# Install dependencies
npm install

# Configure environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# Edit .env and replace 192.168.x.x with your machine's LAN IP
# (run `ipconfig` on Windows or `ifconfig` on macOS/Linux to find it)

# Start Expo
npx expo start
```

Then scan the QR code with **Expo Go** on your Android/iOS device (must be on the same Wi-Fi network as your machine).

---

## Environment Variables Reference

### Root `.env` (Docker Compose + Backend)

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | Database host (`db` in Docker, `localhost` locally) | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `EMSNew` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `yourpassword` |
| `JWT_SECRET` | Secret key for signing JWT tokens | `long_random_string` |
| `JWT_ACCESS_EXPIRATION_MS` | Access token lifetime in ms | `900000` (15 min) |
| `JWT_REFRESH_EXPIRATION_MS` | Refresh token lifetime in ms | `8640000000` (100 days) |
| `MAIL_USERNAME` | Gmail address for sending emails | `hr@yourcompany.com` |
| `MAIL_PASSWORD` | Gmail App Password (16 characters) | `abcd efgh ijkl mnop` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |
| `COOKIE_SECURE` | `true` for HTTPS production deployments | `false` |
| `COOKIE_SAME_SITE` | Cookie SameSite policy | `Lax` (dev) / `None` (prod) |
| `GROQ_API_KEY` | Groq API key for Aura AI chatbot | `gsk_...` |
| `PORT` | Backend server port | `8000` |
| `VITE_API_BASE_URL` | API base URL passed to frontend build | `/api` |

### `ems-frontend/.env` (Vite dev server only)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | API base path (proxied locally) | `/api` |
| `VITE_SESSION_TIMEOUT_MS` | Idle session timeout in ms | `900000` |
| `BACKEND_URL` | Backend URL for Vite proxy (not in bundle) | `http://localhost:8000` |

### `ems-frontendnative/.env` (Expo)

| Variable | Description | Example |
|----------|-------------|---------|
| `EXPO_PUBLIC_API_URL` | Full backend URL for the mobile app | `http://192.168.1.42:8000/api` |
| `REACT_NATIVE_PACKAGER_HOSTNAME` | LAN IP for Metro bundler | `192.168.1.42` |

---

## Default Login

When the backend starts for the first time it seeds a default admin account:

| Field | Value |
|-------|-------|
| Employee ID | `TT0001` |
| Password | `admin@123` |

> **Change this password immediately after first login.**

---

## Deployment on Render

The project includes a `render.yaml` blueprint at the repo root that provisions:
- A **managed PostgreSQL** database (`ems-postgres`)
- A **Docker web service** for the backend (`ems-backend`)
- A **static site** for the React frontend (`ems-frontend`)

After deploying, set the following secrets in the Render Dashboard under each service's **Environment** tab:
- `GROQ_API_KEY`
- `MAIL_PASSWORD`
- `JWT_SECRET` (recommended: change from the default)
