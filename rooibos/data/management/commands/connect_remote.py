from django.core.management.base import BaseCommand
from rooibos.data.models import Collection, RemoteMetadata
from rooibos.storage.models import Storage


class Command(BaseCommand):
    help = 'Create remote metadata '

    def add_arguments(self, parser):
        parser.add_argument('--metadata-url', '-d', dest='metadata_url',
                            help='URL of metadata file'),
        parser.add_argument('--mapping-url', '-m', dest='mapping_url',
                            help='URL of mapping file'),
        parser.add_argument('--collection', '-c', dest='collection_id',
                            type=int,
                            help='Identifier of existing collection'),
        parser.add_argument('--storage', '-s', dest='storage_id', type=int,
                            help='Identifier of existing storage'),
        parser.add_argument('--title', '-t', dest='title',
                            help='Title of new collection and storage'),
        parser.add_argument('--storage-type', '-y', dest='storage_type',
                            help='Type of new storage (local, s3, b2, etc.)'),
        parser.add_argument('--storage-base', '-b', dest='storage_base',
                            help='Base of new storage'),
        parser.add_argument('--credential-id', '-u', dest='credential_id',
                            help='Credential ID of new storage'),
        parser.add_argument('--credential-key', '-p', dest='credential_key',
                            help='Credential key of new storage'),

    def handle(self, *args, **kwargs):

        if kwargs['collection_id']:
            collection = Collection.objects.get(id=kwargs['collection_id'])
        else:
            collection = Collection.objects.create(title=kwargs['title'])

        if kwargs['storage_id']:
            storage = Storage.objects.get(id=kwargs['storage_id'])
        else:
            storage = Storage.objects.create(
                title=kwargs['title'],
                system=kwargs['storage_type'],
                base=kwargs['storage_base'],
                credential_id=kwargs['credential_id'],
                credential_key=kwargs['credential_key'],
            )

        metadata = RemoteMetadata.objects.create(
            collection=collection,
            storage=storage,
            url=kwargs['metadata_url'],
            mapping_url=kwargs['mapping_url'],
        )

        print('Created %r' % metadata)
