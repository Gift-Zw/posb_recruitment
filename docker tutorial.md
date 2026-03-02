## Docker tutorial (deep dive) — POSB Recruitment Portal

This guide explains Docker from the ground up, then applies everything to this Django project (`hr_onboarding`) with practical examples, common workflows, and troubleshooting.

---

## What Docker is (and what it is not)

### What Docker solves
- **“Works on my machine”**: your app runs the same way on every server/laptop because it ships with its runtime and dependencies.
- **Repeatable builds**: you can rebuild the same image at any time.
- **Isolation**: each app can run with its own Python version and libraries.
- **Simple deployment unit**: the unit you deploy is an **image**, and what runs is a **container**.

### What Docker is NOT
- Not a full VM (containers share the host OS kernel).
- Not magic for stateful data (DBs/uploads need volumes or external storage).
- Not automatically “production-ready” without proper configuration (networking, secrets, reverse proxies, TLS, logging, etc.).

---

## Core concepts you must know

### Image
An **image** is a packaged filesystem + metadata (layers) used to create containers.
- Built from a `Dockerfile`.
- Immutable: you don’t “edit” images; you rebuild them.

### Container
A **container** is a running (or stopped) instance of an image.
- Containers are ephemeral: if you delete the container, anything inside that wasn’t persisted is gone.

### Dockerfile
Defines how to build an image. It’s like a recipe:
- Start from a base image (e.g. Python).
- Install OS dependencies (e.g. libpq-dev).
- Install Python dependencies (`pip install -r requirements.txt`).
- Copy your application code.
- Define how it runs (entrypoint/CMD).

### Volume
A **volume** is persistent storage managed by Docker.
- Use volumes when you need data to survive container restarts/rebuilds.
- Examples: DB data, user uploads (`MEDIA_ROOT`), collected static (`STATIC_ROOT`).

### Network
Docker creates networks so containers can reach each other.
- In Compose, a service can reach another by **service name** (e.g. `db`).
- When using an **external DB**, you connect via its hostname/IP.

### Docker Compose
Compose runs multi-container apps using `docker-compose.yml` (or `docker compose`).
- Defines services (web, db, redis, etc.), networks, volumes, environment, ports, build context, and dependencies.

---

## How Docker applies to this Django project

This project is a server-rendered Django app that:
- Uses **PostgreSQL** via `DB_*` environment variables in `posb_recruitment/settings.py`.
- Uses `django-environ` to load `.env`.
- Uses `STATIC_ROOT=/app/staticfiles` and `MEDIA_ROOT=/app/media`.

We dockerized it with:
- `Dockerfile` (builds the app image)
- `docker-entrypoint.sh` (runs migrations + collectstatic before starting the server)
- `docker-compose.yml` (runs the `web` container; you chose external DB)
- `.dockerignore` (keeps builds small and avoids leaking secrets)

---

## Deep dive: the `Dockerfile` (what each part means)

Your `Dockerfile` (high-level intent):
- Use Python 3.12 (required by Django 6).
- Install system packages needed for Postgres libs.
- Install Python packages.
- Copy the project.
- Run an entrypoint script that prepares the app (migrations/static), then runs gunicorn.

### Base image: `python:3.12-slim`
- **Why**: small Debian-based image, includes Python 3.12.
- **Trade-off**: slim images sometimes require you to install build/runtime libs explicitly (we did).

### Environment flags
- `PYTHONDONTWRITEBYTECODE=1`: avoids `__pycache__` .pyc generation in the container.
- `PYTHONUNBUFFERED=1`: logs flush immediately (useful for `docker logs`).

### System packages for Postgres
We install:
- `libpq-dev` and `gcc`

**Why**:
- Some Python packages (especially DB drivers) may require native libs.
- Ensures reliable installs and runtime linking.

### Dependency install layering (caching)
We copy `requirements.txt` first, install deps, then copy app code.

**Why**:
- Docker caches layers. Most code changes won’t invalidate the dependency layer.
- Rebuilds become much faster.

### Entrypoint
We copy `docker-entrypoint.sh`, make it executable, and normalize line endings:
- **Why CRLF fix**: if you edit files on Windows, line endings can be `\r\n`. Linux shells can choke on `\r`.

### Gunicorn as the runtime server
Gunicorn runs the WSGI app:
- `posb_recruitment.wsgi:application`

**Why not `runserver`**:
- `runserver` is for dev only (not designed for production traffic).
- gunicorn is stable and commonly used behind Nginx/Traefik.

---

## Deep dive: the entrypoint script (why we need it)

`docker-entrypoint.sh` does “startup tasks”:

### 1) Wait for DB connectivity
Why:
- Containers may start in parallel.
- If Django runs migrations before DB is reachable, startup fails.

When using an external DB:
- This wait step still helps if the DB is reachable over the network.
- If your DB is behind strict firewall rules, it will keep waiting until it can connect.

### 2) `python manage.py migrate --noinput`
Why:
- Ensures your schema matches your models every time you deploy.
- Avoids “forgot to migrate” downtime.

### 3) `python manage.py collectstatic`
Why:
- Django static files need to be collected into `STATIC_ROOT` for production-style serving.
- We run it at container start because build-time collectstatic can fail without correct env vars.

### 4) `exec "$@"`
Why:
- Makes gunicorn the main process (PID 1) so signals work correctly (graceful shutdown on restart).

---

## Deep dive: `docker-compose.yml` (external DB version)

You asked to remove the Postgres container, so Compose now only runs the `web` service.

### What Compose is doing for you
- **Build** the app image from the Dockerfile.
- **Inject env vars** into the container using `.env`.
- **Expose port 8000** so your host can reach the container (`http://host:8000`).
- **Persist media/static** via named volumes so user uploads/static don’t disappear on rebuild.

### Key env vars for external Postgres
Your `.env` must point to the external DB:

```env
DB_HOST=your-db-host-or-ip
DB_PORT=5432
DB_NAME=recruitment_portal
DB_USER=postgres
DB_PASSWORD=your-db-password
```

Also ensure:
- `ALLOWED_HOSTS` includes your server hostname/IP (you already did for `170.9.240.189` in your server env).

---

## How to run this project with Docker (day-to-day)

### Build and start

```bash
docker compose build
docker compose up -d
```

### View logs

```bash
docker compose logs -f web
```

### Shell into the container

```bash
docker compose exec web bash
```

### Run Django management commands

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Stop / remove containers

```bash
docker compose down
```

### Rebuild after dependency changes
If you change `requirements.txt`:

```bash
docker compose build --no-cache
docker compose up -d
```

---

## Local development vs production patterns (important)

### Development pattern
Common dev choice: mount your source code into the container so changes reflect without rebuild.
- We did **not** enable code bind-mount by default (safer for deployment).
- If you want it for dev, we can add a `docker-compose.dev.yml` that mounts `.:/app` and uses `runserver`.

### Production pattern
Common prod choice:
- build a versioned image (tag it)
- run gunicorn behind a reverse proxy (Nginx/Traefik/Caddy)
- serve static via Nginx or object storage
- store media in a volume or object storage (S3-compatible)
- use secrets manager (not `.env` in repo)

---

## Networking: “Why does localhost not work in Docker?”

Inside a container:
- `localhost` means **the container itself**, not your server host.

So:
- If Postgres runs in another container: set `DB_HOST=db` (service name).
- If Postgres runs externally: set `DB_HOST=<db-server-hostname-or-ip>`.

---

## Volumes in this project (what should persist)

### `media` volume
Persists uploads at `/app/media` (Django `MEDIA_ROOT`).
- Without it: uploads disappear when container is recreated.

### `staticfiles` volume
Persists `/app/staticfiles` (Django `STATIC_ROOT`).
- Useful if you run `collectstatic` at startup and want the output to persist.

If you later serve static from Nginx or a CDN/object storage, you may remove the `staticfiles` volume and handle static externally.

---

## Environment variables, `.env`, and secrets (best practices)

### What belongs in `.env`
- DB connection info (host/port/user/pass/dbname)
- SECRET_KEY
- Email credentials (if needed)
- Allowed hosts / site URL

### What should NOT be committed
- `.env` itself (real secrets)

You created `.env.example` so teammates can copy it and fill in real values.

---

## Common errors and how to fix them

### 1) “DisallowedHost”
Symptom:
- `Invalid HTTP_HOST header: 'x.x.x.x'`

Fix:
- Add the host/IP to `ALLOWED_HOSTS` in `.env`, then restart the container:

```bash
docker compose up -d
```

### 2) DB connection errors
Symptoms:
- `could not connect to server`
- `timeout expired`

Checklist:
- DB host/port reachable from your Docker host
- firewall/security group allows inbound from Docker host IP
- credentials correct
- `DB_HOST` is not `localhost` unless DB is on the same network namespace (rare)

### 3) Migrations fail at startup
Symptoms:
- container exits and restarts

Fix:
- inspect logs:

```bash
docker compose logs --tail=200 web
```

Often the issue is missing env vars or DB access.

### 4) Static not loading
Causes:
- `collectstatic` not running (or failing)
- not serving static in front of gunicorn in production

Notes:
- Django can serve static in DEBUG mode, but production should serve static via a reverse proxy or configured static hosting.

---

## Example: production-ish deployment on a server (simple)

If you’re on a server and want to run the container on port 8000:

1) Put `.env` on the server (not in git)
2) Start containers:

```bash
docker compose up -d --build
```

3) Put Nginx in front (optional) to serve HTTPS and proxy to `localhost:8000`.

---

## Quick glossary (so terms stick)
- **Build**: create an image from Dockerfile (`docker build`, `docker compose build`)
- **Run**: start containers from images (`docker run`, `docker compose up`)
- **Tag**: label images (`myapp:1.0.0`)
- **Layer**: cached build step inside an image
- **Volume**: persistent storage independent of container lifecycle
- **Service**: a Compose-defined container configuration (web/db/etc.)

---

## Next improvements (optional)

If you want an even cleaner setup, we can add:
- **Healthcheck for `web`**
- **Separate dev compose file** (bind-mount code + runserver)
- **Nginx container** for static + reverse proxy
- **Non-root user** in Dockerfile for security hardening
- **CI build** on GitHub Actions to publish images to GHCR/DockerHub

