# Ruoom

A [Django](https://docs.djangoproject.com) project.

## Index

- [Conventions](#conventions)
- [Initialization](#initialization)
- [Statics](#statics)

## Conventions

- Copy `.env.example` to `.env` and replace deployment-specific values.

## Initialization

By default, Core uses SQLite at `db.sqlite3`, so a local installation does not
need a separate database service. To use PostgreSQL or another explicitly
configured backend, set `DATABASE_URL` in `.env` using a supported URL scheme.
For example:

```
DATABASE_URL=postgresql://ruoom_admin:password@localhost:5432/Ruoom
```

Then run:

```
Copy-Item .env.example .env
python manage.py migrate
```

SQLite is convenient for local development and disposable deployments. Use a
durable PostgreSQL database for production applications with important data or
multiple application instances.

For the first deployed business, set `RUOOM_BUSINESS_1_URL` to the public URL
for business 1, then register it after migrations:

```
python manage.py bootstrap_business_domain
```

The command is safe to run repeatedly. Changing `RUOOM_BUSINESS_1_URL` and
running the command again updates business 1's domain mapping. The business
name can be completed after signing in for the first time. If the setting is
empty, the command does nothing.

Now you are ready to create an initial account at the configured URL.

## Railway deployment

Railway deployments use the checked-in `Dockerfile`, `start.sh`, and
`railway.json`. The startup script runs migrations, registers the business
domain, collects static files, and then starts Gunicorn.

For a Railway Bucket, set `STORAGE=S3`, `AWS_S3_BUCKET_NAME`,
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION=auto`,
`AWS_ENDPOINT_URL=https://storage.railway.app`, and
`AWS_S3_URL_STYLE=virtual`. The application accepts both Railway's variable
names and the equivalent django-storages names. Uploaded files use the private
bucket, while public static assets remain same-origin through WhiteNoise.

