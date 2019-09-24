from django.core.management.base import BaseCommand
from rooibos.data.models import FieldSet, FieldSetField, Collection
from rooibos.solr.views import _get_browse_fields, _get_facet_fields


class Command(BaseCommand):
    help = """
Creates default fieldsets for all collections to allow further
configuration for limiting browse and faceted search fields
"""

    def get_or_create_fieldset(self, name, fields):
        fieldset, created = FieldSet.objects.get_or_create(
            name=name,
            defaults={
                'title': name
            }
        )
        if created:
            for field in fields:
                FieldSetField.objects.create(fieldset=fieldset, field=field)
        return fieldset, created

    def handle(self, *args, **kwargs):
        # Create faceted search fieldset
        fieldset, created = self.get_or_create_fieldset(
            'facet-fields', _get_facet_fields())
        if created:
            print("Created facet-fields")
        else:
            print("facet-fields already exists")

        # Create browse fieldset for each collection
        for collection in Collection.objects.filter(owner=None):
            name = 'browse-collection-%s' % collection.id
            fieldset, created = self.get_or_create_fieldset(
                name, _get_browse_fields(collection.id))
            if created:
                print("Created %s" % name)
            else:
                print("%s already exists" % name)
