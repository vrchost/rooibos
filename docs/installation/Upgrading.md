# Upgrading to MDID 3.6 from earlier versions of MDID 3

Due to the new method of installing MDID 3.6 it is strongly recommended to
perform a new installation and then put the database and images in place.

* Follow the installation steps outlined for your operating system
* Change the database settings in `config/settings.py` to point to your
  existing database
* Run `mdid migrate` to migrate the database
* Run `mdid solr reindex` to refresh the full-text index

# Upgrading from MDID2

* Perform a new installation with a blank database.
* Copy the `config.xml` file from your MDID2 installation to a place accessible
  from the new installation.
* If necessary, adjust the `<database>` section in the `config.xml` file so
  that it can be used to connect to the database from the new installation.
* Run `mdid mdid2migrate path/to/config.xml`
* Copy the full-size images from the MDID2 installation to a place accessible
  to the new installation.
* In MDID3, under Management>Manage Storages, fix the paths to the different
  storage directories.
* Run a full re-index with `mdid solr reindex`.
