# Weather API

A weather backend built with **FastAPI**. Users register, verify their email, and then get current weather, forecasts, air quality and severe-weather alerts for any city. They can also save favorite cities and review their search history.

## Features

- **Authentication**: email verification, JWT access and refresh tokens with rotation, logout with token blacklisting, password change, and OTP-based password reset
- **Account protection**: failed-login lockout (5 attempts locks the account for 15 minutes) and per-endpoint rate limiting
- **Weather**: current conditions by city or coordinates, forecast, air quality, severe-weather alerts, and temperature unit conversion
- **Favorites**: up to 10 saved cities per user, with a default city
- **Search history**: paginated history of a user's searches
- **Background jobs**: verification, OTP, login-notification and severe-alert emails are sent by Celery workers
- **Caching**: weather responses are cached in Redis (default 10 minutes)
- **Admin bootstrap**: an admin user is created on startup from environment variables

## Tech stack

| Area | Technology |
| --- | --- |
| Framework | FastAPI, Uvicorn / Gunicorn |
| Database | MySQL (SQLAlchemy 2 async, `asyncmy`), Alembic migrations |
| Cache, rate limits, token store | Redis |
| Background jobs | Celery (Redis broker) |
| Auth | PyJWT, Argon2 password hashing |
| Weather data | OpenWeatherMap |
| Email | SMTP via `aiosmtplib`, Jinja2 templates |
| Tests | pytest, pytest-asyncio, httpx |
| Deployment | Docker, Docker Compose, Nginx |

## Project structure

```
weather_api/
├── app/
│   ├── main.py               # FastAPI app, middleware, routers, health check
│   ├── controller/           # Route handlers: auth, users, weather, favorites, history
│   ├── services/             # Business logic and weather/email providers
│   ├── repositories/         # Database access
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── core/                 # Config, database, Redis, security (JWT, hashing)
│   ├── middleware/           # Request logging and rate limiting
│   ├── celery_server/        # Celery app and email tasks
│   ├── templates/            # HTML email templates
│   ├── alembic/              # Database migrations
│   ├── admin/                # Admin user bootstrap
│   ├── error_handler_server/ # Global error handlers
│   └── utils/                # Auth dependencies
├── tests/                    # Test suite
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── alembic.ini
```

## Configuration

Copy the example file and fill it in:

```bash
cp .env.exaple .env
```

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | MySQL URL, e.g. `mysql+asyncmy://user:password@localhost:3306/weather_app` |
| `REDIS_URL` | Redis URL, e.g. `redis://localhost:6379` |
| `SECRET_KEY` | Long random string used to sign JWTs. **Keep it private** |
| `OPENWEATHERMAP_API_KEY` | Key from [OpenWeatherMap](https://openweathermap.org/api) |
| `WEATHERAPI_KEY` | Key from [WeatherAPI](https://www.weatherapi.com). Required by the settings, but weather data currently comes from OpenWeatherMap |
| `SMTP_USER`, `SMTP_PASSWORD` | Account used to send emails (`SMTP_HOST` / `SMTP_PORT` default to Gmail) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FIRST_NAME`, `ADMIN_LAST_NAME` | Admin account created on first startup |
| `TEST_DATABASE_URL`, `TEST_REDIS_URL` | Database and Redis used by the tests (a SQLite file and Redis DB 15 by default) |
| `DEBUG` | `True` logs SQL statements |

Optional settings (defaults shown): `WEATHER_CACHE_TTL=600`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`.

## Running with Docker

```bash
cp .env.exaple .env                      # then edit it
docker compose up -d --build
docker compose exec api alembic upgrade head
```

This starts the API, a Celery worker, MySQL, Redis and Nginx. Open the interactive docs at **http://localhost/api/v1/docs**.

Inside Docker, `DATABASE_URL` and `REDIS_URL` are set automatically to the container hostnames. MySQL credentials can be changed with `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` and `MYSQL_ROOT_PASSWORD` in `.env`.

## Running locally

Requires Python 3.12, MySQL and Redis.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head
uvicorn app.main:app --reload
```

In a second terminal, start the worker so emails are sent:

```bash
celery -A app.celery_server.celery_instance.celery_app worker --loglevel=info
```

## API overview

All routes are under `/api/v1`. Full details are in the interactive docs at `/api/v1/docs`.

| Area | Endpoints |
| --- | --- |
| Health | `GET /health` |
| Auth | `POST /auth/register`, `GET /auth/verify-email`, `POST /auth/register/resend-email`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `PATCH /auth/password`, `POST /auth/forget-password`, `POST /auth/verify-otp`, `POST /auth/reset-password` |
| Users | `GET /users/me`, `PUT /users/me`, `DELETE /users/me` |
| Weather | `GET /weather/current`, `GET /weather/current/coordinates`, `GET /weather/forecast`, `GET /weather/air-quality`, `GET /weather/alerts`, `POST /weather/convert` |
| Favorites | `GET /favorites/`, `POST /favorites/`, `PUT /favorites/{id}/default`, `GET /favorites/{id}/weather`, `DELETE /favorites/{id}` |
| History | `GET /historys/`, `DELETE /historys/` |

Everything except `/health` and the auth routes needs a bearer token.

### Example

```bash
# 1. Register, then click the link in the verification email
curl -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"SecurePass1","first_name":"Jane","last_name":"Doe","preferred_unit":"metric"}'

# 2. Log in (form data; the username field is the email)
curl -X POST http://localhost/api/v1/auth/login \
  -d "username=jane@example.com&password=SecurePass1"

# 3. Get the weather
curl "http://localhost/api/v1/weather/current?city=Lagos" \
  -H "Authorization: Bearer <access_token>"
```

`preferred_unit` is `metric` (°C) or `imperial` (°F). Send `?unit=` on a weather request to override it.

## Running the tests

The tests need a local Redis server (they use database 15 and flush it). They use a SQLite database, mock Celery, and turn rate limiting off.

```bash
redis-server --daemonize yes
pytest
```

## Author

**Joshua Oguejiofor**
