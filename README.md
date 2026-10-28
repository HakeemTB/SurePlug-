# SurePlug

SurePlug is a campus-focused local product marketplace. The MVP uses Django REST Framework for the API and React, TypeScript, Vite, and Tailwind CSS for the web app.

## Run locally

Use two terminals from the project folder.

### Backend

```powershell
cd backend
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 127.0.0.1:8000
```

The API health endpoint is [http://127.0.0.1:8000/api/v1/health/](http://127.0.0.1:8000/api/v1/health/).

### Frontend

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open [http://127.0.0.1:5173/](http://127.0.0.1:5173/). Vite proxies `/api` to the local Django server.

## Demo vendor accounts

The seed command creates these accounts on first run:

- `sureplug_demo_bites`
- `sureplug_demo_style`
- `sureplug_demo_tech`

The local-only default password is `SurePlugDemo123!`. Override it on first seed with `python manage.py seed_demo_data --password "your-local-password"` or the `SUREPLUG_DEMO_PASSWORD` environment variable. The seed command does not reset passwords for existing users.

Demo accounts and passwords are for local development only. Do not deploy them or use the default password in a shared environment.

## Useful checks

```powershell
cd backend
python manage.py check
python manage.py test accounts products moderation
python manage.py makemigrations --check --dry-run
```

```powershell
cd frontend
npm run build
```

## Production deployment

The repository supports a platform-neutral split deployment: build the React app as static assets, and serve Django through Gunicorn on a Linux/PaaS WSGI host. Configure the static host or reverse proxy to serve the frontend at `/` and route `/api/`, `/media/`, and `/admin/` (if enabled) to Gunicorn on the same public origin. The `/media/` route is required because Django's image serializers return relative `/media/...` paths; without it, product and vendor images will fail to load when the frontend is served by a separate static host. Same-origin routing is required for the session-cookie dashboard flow.

### Backend release

From `backend/`, install `requirements.txt` and set these environment variables in the host's secret/configuration settings:

- `DEBUG=False`
- `SECRET_KEY`: a unique high-entropy secret; never use the development fallback or commit this value.
- `ALLOWED_HOSTS`: comma-separated backend/public hostnames without schemes.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`: production PostgreSQL connection settings.
- `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`: exact HTTPS origins only when the browser frontend is hosted on a different origin. Prefer same-origin proxying and leave these unset.
- `MEDIA_ROOT`: a persistent writable storage path for user-uploaded product/vendor images.
- `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` for HTTPS.

The included `backend/Procfile` starts Gunicorn and runs migrations as a release step. Configure the deployment platform's health check to request `/api/v1/health/`. Run `python manage.py collectstatic --noinput` during the build/release; WhiteNoise serves Django static assets. User-uploaded media is not suitable for ephemeral local disk—mount persistent storage or configure object storage before enabling uploads in production.

Set `SECURE_HSTS_SECONDS` only after HTTPS is working on every relevant host. `TRUST_PROXY_SSL_HEADER=True` is only appropriate when the trusted reverse proxy overwrites `X-Forwarded-Proto`; do not accept that header directly from untrusted clients. Never run `seed_demo_data` in a production environment.

### Frontend release

From `frontend/`, run `npm ci` and `npm run build`, then publish `dist/` through the static host/reverse proxy. Configure SPA fallback to `index.html` and proxy `/api/` and `/media/` to the backend. If the frontend and API must use separate origins, provide exact origins in both CORS and CSRF settings and verify cookie `SameSite`/HTTPS behavior for the chosen deployment domains.

The checked-in `backend/.env.example` is a local development template; Django does not automatically load it. Production values belong in the deployment platform's environment/secret manager.

## Work log

Implementation progress and validation are recorded in [WORK_LOG.md](./WORK_LOG.md).
