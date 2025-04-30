# Ruoom

A [Django](https://docs.djangoproject.com) project.

## Index

- [Conventions](#conventions)
- [Initialization](#initialization)
- [Statics](#statics)

## Conventions

- replace `.sample` with your actual environment file.

## Initialization

To set up the database, initialize PostgreSQL with a database called "Ruoom", a user called "ruoom_admin" and password "password".
Then run the following commands:

```
python manage.py migrate
```

* Now you are ready to create an initial account at localhost:8000

