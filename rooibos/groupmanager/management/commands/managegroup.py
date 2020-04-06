from itertools import chain
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from rooibos.storage.models import Storage
from rooibos.data.models import Collection
from rooibos.access.models import AccessControl, ContentType


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--name', '-n', dest='usergroup',
                    help='Name of user group to be managed')
        parser.add_argument('--storage', '-s', dest='storagepath',
                    help='Create storage at specified path')
        parser.add_argument('--storageurlbase', dest='storageurlbase',
                    help='Storage URL base')
        parser.add_argument('--storageserverbase', dest='storageserverbase',
                    help='Storage server base')
        parser.add_argument('--collection', '-c', dest='createcollection',
                    action='store_true', help='Create collection')
        parser.add_argument('--collectiongroup', '-g', dest='collectiongroup',
                    help='Name of optional collection group')
        parser.add_argument('--users', '-u', dest='users',
                    help='Comma-separated list of usernames for group ' +
                    '(removes all others)')
        parser.add_argument('--adduser', '-a', dest='addusers', action='append',
                    help='Add user(s) to group (comma-separated list ' +
                    'or repeated argument')
        parser.add_argument('--removeuser', '-r', dest='removeusers', action='append',
                    help='Remove user(s) from group (comma-separated list ' +
                    'or repeated argument')
        parser.add_argument('--createusers', dest='createusers', action='store_true',
                    help='Create missing user accounts. If specified, list ' +
                    'users as username:email:firstname:lastname:password ' +
                    'with anything other than username being optional')

    help = "Creates groups, manages memberships and optionally creates " + \
           "associated storage and collection"

    def handle(self, *args, **kwargs):

        usergroup = kwargs.get('usergroup')
        storagepath = kwargs.get('storagepath')
        storageurlbase = kwargs.get('storageurlbase')
        storageserverbase = kwargs.get('storageserverbase')
        createcollection = kwargs.get('createcollection')
        collectiongroup = kwargs.get('collectiongroup')
        users = kwargs.get('users')
        addusers = kwargs.get('addusers')
        removeusers = kwargs.get('removeusers')
        createusers = kwargs.get('createusers')

        def message(msg):
            if 'output' in kwargs:
                kwargs['output'].append(msg)
            else:
                print(msg)

        if not usergroup:
            message("--name is a required parameter.")
            return

        group, created = Group.objects.get_or_create(name=usergroup)

        def process_users(users, action, create=True):
            for data in chain(*(u.split(',') for u in users)):
                user, email, first, last, pwd = (data + '::::').split(':')[:5]
                try:
                    action(User.objects.get(username=user))
                except User.DoesNotExist:
                    if not createusers or not create:
                        message("User '%s' not found, ignored." % user)
                    else:
                        newuser = User(username=user, email=email,
                                       first_name=first, last_name=last)
                        if pwd:
                            newuser.set_password(pwd)
                        newuser.save()
                        action(newuser)

        if users:
            group.user_set.clear()
            process_users([users], group.user_set.add)
        if addusers:
            process_users(addusers, group.user_set.add)
        if removeusers:
            process_users(removeusers, group.user_set.remove, create=False)

        if createcollection:
            collection, created = Collection.objects.get_or_create(
                title=usergroup,
            )
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Collection),
                object_id=collection.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                    write=True,
                )
            )
        else:
            collection = None

        if collectiongroup:
            parent_collection, created = Collection.objects.get_or_create(
                title=collectiongroup,
            )
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Collection),
                object_id=parent_collection.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                )
            )
            if collection:
                parent_collection.children.add(collection)

        if storagepath:
            storage, created = Storage.objects.get_or_create(
                title=usergroup,
                defaults=dict(
                    system='local',
                    base=storagepath,
                    urlbase=storageurlbase,
                    deliverybase=storageserverbase,
                )
            )
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Storage),
                object_id=storage.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                    write=True,
                )
            )
