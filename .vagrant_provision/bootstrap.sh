#!/usr/bin/env bash
##############################################################################
# A Vagrant provisioning shell script to setup an MDID Development VM
##############################################################################
# Update our apt sources
apt-get update

# Make sure we are starting from an up-to-date system
apt-get upgrade -y

##############################################################################
# Install MySQL
##############################################################################
# The mysql-server package interactively prompts for the root pasword to the
# MySQL server.  These commands will cache the password settings, and they
# will be used by the mysql-server package on installation.  Since this is
# pretty insecure anyway, no attempt is made at using a secure password :)
#
# Sets the MySQL root password to 'mdid'
echo mysql-server mysql-server/root_password password mdid | debconf-set-selections
echo mysql-server mysql-server/root_password_again password mdid | debconf-set-selections

# Now we can install the packages
# mysql-server: The MySQL server
# mysql-client: The MySQL client utilities
# libmysqlclient-dev: MySQL developmental libraries, needed to build the python
#   MySQL module
apt-get install -y mysql-server mysql-client libmysqlclient-dev

##############################################################################
# Install other dependencies
##############################################################################
# Java is needed to run Solr
apt-get install -y openjdk-7-jre-headless

# RabbitMQ is needed to manage the worker jobs
apt-get install -y rabbitmq-server

# Memcached is used for ???
apt-get install -y memcached

##############################################################################
# Setup init scripts for Solr
##############################################################################
# use sysv-rc-conf to manage runlevels
apt-get install -y sysv-rc-conf

# the solr init script will be copied to the /etc/init.d dir with vagrant file
# provisioning
# TODO: set runlevels for the solr init script and start the service

##############################################################################
# Python build dependencies
##############################################################################
# Need the python development libs
apt-get install -y python-dev

# PyODBC needs the unixodbc libs
apt-get install -y unixodbc unixodbc-dev

# python-ldap needs ldap and sasl libraries
apt-get install -y libldap2-dev libsasl2-dev

# Pillow needs image libraries
apt-get install -y libtiff5-dev libjpeg8-dev zlib1g-dev

##############################################################################
# Configure Python and setup a Virtual Environment
##############################################################################
# Use PIP for python package management
apt-get install -y python-pip

# install virtualenv
pip install virtualenv

# move into our project dir
cd /vagrant

# create a virtual environment (if needed)
[[ ! -d venv/ ]] && virtualenv venv

# enter our virtual environment
source venv/bin/activate

# install our requirements
pip install -r requirements.txt

##############################################################################
# Configure MDID
##############################################################################
# create the MDID database
mysql -uroot -pmdid < .vagrant_provision/create_database.sql

# create the local settings
cd rooibos
cp settings_local_template.py settings_local.py
# TODO: what all can we programatically set in the settings file, and what do
#       we need to do manually?

# setup the database
python manage.py syncdb --noinput
python manage.py createcachetable cache
