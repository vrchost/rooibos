# Upgrading from MDID 3.2 or later

To upgrade an installation of MDID 3.2 or later, just replace the old
package folder with the new package, keeping your `rooibos_settings` and
any other custom files and folders in place.

Afterwards, run `django-admin migrate` to apply any database changes.


# Upgrading from MDID 3.0 or 3.1

Perform a new installation pointing to your existing database and image files.

Afterwards, run

    django-admin migrate --fake-initial
    django-admin migrate

If you receive an error

    Unknown column 'data_collection.order' in 'field list'

run this command against your MySQL database from within the MySQL shell:

    ALTER TABLE data_collection ADD COLUMN `order` INT NULL DEFAULT 0;

If you receive an error

    Error creating new content types

run this command against your MySQL database from within the MySQL shell:

    ALTER TABLE django_content_type DROP COLUMN name


# Upgrading from MDID2

* Perform a new installation with a blank database.
* Copy the `config.xml` file from your MDID2 installation to a place accessible
  from the new installation.
* If necessary, adjust the `<database>` section in the `config.xml` file so
  that it can be used to connect to the database from the new installation.
* Run `django-admin mdid2migrate path/to/config.xml`
* Copy the full-size images from the MDID2 installation to a place accessible
  to the new installation.
* In MDID3, under Management>Manage Storages, fix the paths to the different
  storage directories.
* Run a full re-index with `django-admin solr reindex`.
