#!/usr/bin/env bash

cd /app
python3 manage.py migrate --noinput
if [[ ${MODE:-prod} == "dev" ]]
then
	python3 manage.py collectstatic --noinput
	exec python3 manage.py runserver 0.0.0.0:8000
else
	python3 manage.py collectstatic --noinput
    exec gunicorn --workers 5 --timeout 360 ruoom.wsgi --bind 0.0.0.0:8000 --limit-request-line 0
fi
