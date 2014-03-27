Changes
=======

Key
---

  * [!] - Important note regarding some change.
  * [SETTING] - Changed available settings
  * [MIGRATION] - Change database schema
  * [DEPENDENCY] - Changed dependencies.

Changes
-------

List of significant changes, with the latest at the top:

  * 2014/03/27

    [MIGRATION]
    **Shared collections.** A new table is required to manage remote shared
    collections.  Run `python manage.py syncdb`.

    [DEPENDENCY]
    **New job manager.** MDID now uses RabbitMQ to run background jobs and to
    instantly update the Solr full-text index.  You must [install RabbitMQ](http://www.rabbitmq.com/download.html).

    [DEPENDENCY]
    **New Python library dependencies.** Check `requirements.txt` for newly
    added third-party library dependencies.

  * 2013/10/20

    [SETTING]
    **Custom master template.**  It is now possible to insert custom changes into
    the master template.  Create a new template custom template by extending
    `master_root.html` and setting `MASTER_TEMPLATE` in `settings_local.py`.

  * 2013/08/12

    **Changed functionality of IP address based groups.**  Previously IP address
    based groups did not affect anonymous users.  Now, permissions assigned to
    IP address based groups are always in effect, no matter if the user is
    logged in or not.
