#!/usr/bin/env bash
HOME_DIR=`pwd`
VAGRANT_DIR=/vagrant
PROVISION_DIR=$VAGRANT_DIR/.vagrant_provision
MDID_DIR=$HOME_DIR/mdid
MDID_DATA_DIR=$HOME_DIR/mdid_data
ROOIBOS_DIR=$MDID_DIR/rooibos

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
# Setup files and directories
##############################################################################
# create a symlink from /vagrant to our home dir
sudo -u vagrant ln -s $VAGRANT_DIR $MDID_DIR

# create directories for our mdid data
sudo -u vagrant mkdir $MDID_DATA_DIR
# explicitly create the log directory, because when the workers service fires
# up later in the provisioning, if they're not there then they will get
# created by root and permissions will be all jacked up
sudo -u vagrant mkdir -p $MDID_DATA_DIR/scratch/logs

# link in a little helper script for running the django dev server
sudo -u vagrant ln -s $PROVISION_DIR/runserver $HOME_DIR/

##############################################################################
# Configure Python and setup a Virtual Environment
##############################################################################
# Use PIP for python package management
apt-get install -y python-pip

# install virtualenv
pip install virtualenv

# move into our project dir
cd $MDID_DIR

# create a virtual environment (if needed)
[[ ! -d venv.vagrant/ ]] && virtualenv venv.vagrant

# enter our virtual environment
source venv.vagrant/bin/activate

# install our requirements
pip install -r requirements.txt

##############################################################################
# Configure MDID
##############################################################################
# create the MDID database
mysql -uroot -pmdid < .vagrant_provision/create_database.sql

# create the local settings
if [ -f $ROOIBOS_DIR/settings_local.py ]; then
  # backup any existing local settings first
  mv $ROOIBOS_DIR/settings_local.py $ROOIBOS_DIR/settings_local.backup.py
fi
# Get the default gateway IP address so we can add it to INTERNAL_IPS
GATEWAY_IP=`route -n | grep 'UG' | awk '{print $2}'`
# filter our local settings template, replacing necessary values
cat $PROVISION_DIR/settings_local.vagrant.py \
  | sed -e "s/<<GATEWAY_IP>>/$GATEWAY_IP/" \
  > $ROOIBOS_DIR/settings_local.py

# move into the rooibos app directory
cd $ROOIBOS_DIR

# setup the database
python manage.py syncdb --noinput
python manage.py createcachetable cache

##############################################################################
# Add Upstart scripts for Solr and the Workers
##############################################################################
cp $PROVISION_DIR/mdid3-*.conf /etc/init

# start up the services
service mdid3-solr start
service mdid3-workers start
