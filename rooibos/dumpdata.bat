@echo off
python manage.py dumpdata --format=json --indent=2 -e sessions
