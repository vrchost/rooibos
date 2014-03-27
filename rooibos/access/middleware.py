from django.core.exceptions import MiddlewareNotUsed
from django.core.management.color import no_style
from django.db.backends.creation import BaseDatabaseCreation
from django.db import connection
from models import AccessControl, ExtendedGroup, IP_BASED_GROUP
import logging


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
                logging.debug("running query %s" % s)
                cursor.execute(s)
                logging.debug("done")
        except:
            logging.exception("error running query")
            #pass

        try:
            # Remove IP based group members
            for group in ExtendedGroup.objects.filter(type=IP_BASED_GROUP):
                logging.debug("deleting users from group %s" % group.id)
                group.user_set.clear()
                logging.debug("done")
        except:
            logging.exception("error deleting users")
            #pass

        # Only need to run once
        raise MiddlewareNotUsed


class AnonymousIpGroupMembershipMiddleware():

    def process_request(self, request):
        cached_ip = request.session.get('_cached_remote_addr')
        group_ids = request.session.get('_cached_ip_group_memberships', [])
        current_ip = request.META['REMOTE_ADDR']
        if cached_ip != current_ip:
            # find IP based user groups and cache them
            for group in ExtendedGroup.objects.filter(type=IP_BASED_GROUP):
                if group._check_subnet(current_ip):
                    group_ids.append(group.id)
            request.session['_cached_remote_addr'] = current_ip
            request.session['_cached_ip_group_memberships'] = group_ids
            logging.debug('Detected IP address change to %s, found %s IP based groups (%s)' %
                          (current_ip, len(group_ids), ','.join(str(g) for g in group_ids)))
        # also attach to request.user object, since request object
        # is not passed around everywhere
        logging.debug('Updating user object with cached IP based groups (%s)' %
                      ','.join(str(g) for g in group_ids))
        request.user._cached_ip_group_memberships = group_ids
