from django.core.exceptions import MiddlewareNotUsed
from django.core.management.color import no_style
from django.db.backends.creation import BaseDatabaseCreation
from django.db import connection
from models import AccessControl


class AccessOnStart:

    def __init__(self):

        try:
            # Add missing index on object_id on AccessControl table
            creation = BaseDatabaseCreation(connection)
            sql = creation.sql_indexes_for_field(
                AccessControl,
                AccessControl._meta.get_field('object_id'),
                no_style(),
            )
            cursor = connection.cursor()
            for s in sql:
                cursor.execute(s)
        except:
            pass

        # Only need to run once
        raise MiddlewareNotUsed
