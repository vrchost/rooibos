from optparse import make_option
from django.core.management.base import BaseCommand
from rooibos.data.models import Collection
from rooibos.storage.models import Storage
from rooibos.access.models import ExtendedGroup, Subnet, AccessControl, ContentType


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--name', '-n', dest='usergroup',
                    help='Name of user group to be managed'),
        make_option('--subnet', '-s', dest='subnet',
                    help='Subnet for user group, e.g. 192.168.0.0/255.255.0.0'),
    )
    help = "Creates or updates IP address based extended user group "


    def handle(self, *args, **kwargs):

        usergroup = kwargs.get('usergroup')
        subnet = kwargs.get('subnet')

        if not usergroup:
            print "--name is a required parameter"
            return
        if not subnet:
            print "--subnet is a required parameter"
            return

        group, created = ExtendedGroup.objects.get_or_create(name=usergroup, type='I')

        if created:
            print "Created new",
        else:
            print "Updating existing",
        print "user group %s" % usergroup

        subnets = Subnet.objects.filter(group=group)
        if subnets:
            print "Removing %d existing subnet(s)" % len(subnets)
        subnets.delete()

        Subnet.objects.create(group=group, subnet=subnet)
        print "Created subnet %s" % subnet

        for collection in Collection.objects.filter(owner__isnull=True):
            print "Setting read access to collection %s" % collection.name
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Collection),
                object_id=collection.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                )
            )

        for storage in Storage.objects.filter(system__in=('local', 'cloudfiles')):
            print "Setting read access to storage %s" % storage.name
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Storage),
                object_id=storage.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                )
            )
