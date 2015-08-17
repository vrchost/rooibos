Adding a Top Terms screen
===

An optional screen showing the top 500 indexed terms for all metadata in the installation can
be enabled by setting

    SHOW_TERMS = True

in `settings_local.py`.

The screen is disabled by default, since the metadata is exposed to all authenticated users
without regard to the permissions set on the related records and collections, i.e. the users
may see terms that would not otherwise be accessible to them.

Clicking on a term runs a keyword search, which may not return any hits, depending on permissions.
