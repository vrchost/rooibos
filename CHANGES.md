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

  * 2013/08/12

    Changed functionality of IP address based groups.  Previously IP address
    based groups did not affect anonymous users.  Now, permissions assigned to
    IP address based groups are always in effect, no matter if the user is
    logged in or not.
