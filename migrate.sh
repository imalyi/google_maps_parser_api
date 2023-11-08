#!/bin/bash

rm db
rm -r google_maps_parser_api/migrations/

rm -r gmaps/migrations/
#sudo docker-compose up -d

python3 manage.py makemigrations users
python3 manage.py migrate users

python3 manage.py makemigrations google_maps_parser_api
python3 manage.py migrate google_maps_parser_api

python3 manage.py makemigrations gmaps
python3 manage.py migrate gmaps

python3 manage.py makemigrations
python3 manage.py migrate

DJANGO_SUPERUSER_USERNAME=igor \
DJANGO_SUPERUSER_PASSWORD=343877 \
python3 manage.py createsuperuser --noinput

python3 manage.py test
python3 manage.py runserver 0.0.0.0:8000
