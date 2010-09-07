#!/bin/bash
echo You are about to delete your database, please cancel if this is not what you want!
read
mysqladmin -u root --force drop rooibos
mysql -u root -e "CREATE DATABASE rooibos CHARACTER SET utf8"
python manage.py syncdb --noinput
python manage.py createcachetable cache
