#!/bin/bash

docker-compose up -d database
sleep 35
docker run --network docker_default wmit/mdid:3.2 python manage.py syncdb --noinput
docker run --network docker_default wmit/mdid:3.2 python manage.py migrate
docker-compose up -d
