# StandupBot — Docker & Database Setup Guide

This guide walks you through setting up the PostgreSQL database for local development using Docker.

---

## Prerequisites

- **Docker Desktop** installed and running
  - Download: https://www.docker.com/products/docker-desktop
  - After install, ensure Docker is running (whale icon in system tray)

---

## Step-by-Step Setup

### 1. Start the Database

Open a terminal in the **project root** (`StandupBot/`) and run:

```bash
docker compose up -d
```

This will:
- Pull the PostgreSQL 16 Alpine image (if not already cached)
- Create a container named `standupbot-postgres`
- Create the `standupbot` database with user `standupbot` / password `standupbot`
- Create the `standupbot_test` database (for running tests)
- Expose PostgreSQL on port `5432`

### 2. Verify the Database is Running

```bash
docker compose ps
```

You should see:
```
NAME                  STATUS    PORTS
standupbot-postgres   running   0.0.0.0:5432->5432/tcp
```

### 3. Test the Database Connection

```bash
docker exec -it standupbot-postgres psql -U standupbot -d standupbot -c "SELECT 1;"
```

Expected output:
```
 ?column?
----------
        1
(1 row)
```

### 4. Connect from Your Application

The connection string is already configured in `backend/.env.example`:

```
DATABASE_URL=postgresql+asyncpg://standupbot:standupbot@localhost:5432/standupbot
```

Copy `.env.example` to `.env` in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

### 5. Run Database Migrations

```bash
cd backend

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Run all migrations
alembic upgrade head
```

---

## Common Commands

### View Database Logs

```bash
docker compose logs -f postgres
```

### Stop the Database

```bash
docker compose stop
```

### Restart the Database

```bash
docker compose restart
```

### Destroy Everything (deletes all data!)

```bash
docker compose down -v
```

> ⚠️ The `-v` flag removes the data volume. All database data will be permanently deleted.

### Connect to PostgreSQL Shell

```bash
docker exec -it standupbot-postgres psql -U standupbot -d standupbot
```

Once inside, useful commands:
```sql
\dt              -- List all tables
\d table_name    -- Describe a table
\l               -- List all databases
\q               -- Quit
```

---

## Resetting the Database

If you need to start fresh:

```bash
# 1. Destroy the container and volume
docker compose down -v

# 2. Recreate everything
docker compose up -d

# 3. Wait for it to be healthy (5-10 seconds)
docker compose ps

# 4. Re-run migrations
cd backend
alembic upgrade head
```

---

## Troubleshooting

### Port 5432 Already in Use

If you have another PostgreSQL instance running on port 5432:

**Option A:** Stop the existing PostgreSQL service:
```bash
# Windows
net stop postgresql-x64-16

# macOS
brew services stop postgresql
```

**Option B:** Change the port in `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Use port 5433 instead
```

Then update your `DATABASE_URL` in `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://standupbot:standupbot@localhost:5433/standupbot
```

### Container Won't Start

```bash
# Check logs for errors
docker compose logs postgres

# Remove and recreate
docker compose down -v
docker compose up -d
```

### Permission Denied

Make sure Docker Desktop is running and your user has Docker permissions.

---

## Database Connection Details

| Property | Value |
|----------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `standupbot` |
| Test Database | `standupbot_test` |
| Username | `standupbot` |
| Password | `standupbot` |
| Connection String | `postgresql+asyncpg://standupbot:standupbot@localhost:5432/standupbot` |
