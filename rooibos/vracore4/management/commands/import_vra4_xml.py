import os.path
import re
from collections import defaultdict
from itertools import count
from xml.etree import ElementTree

import xmlschema
from django.core.management import BaseCommand
from django.db.models import Q

from rooibos.data.models import Collection, standardfield, FieldValue, Record, get_system_field, Field, CollectionItem
from rooibos.vracore4.models import STANDARD_NAMESPACE, STANDARD_MANAGER, VRACore4FieldValue, STANDARD

NAMESPACES = {'vra4': STANDARD_NAMESPACE, 'xml': 'http://www.w3.org/XML/1998/namespace'}

VRA_ATTRIBUTES = (
    'dataDate',
    'extent',
    'href',
    ('xml:lang', 'lang'),
    'pref',
    'refid',
    'rules',
    'source',
    'vocab',
)


class InvalidManager(Exception):
    pass


def strip_namespace(tag):
    return re.sub(r'{.+}', '', tag)


def get_text(element):
    return element.text or '' if element is not None else ''


def snake_case(text):
    return re.sub(r'([A-Z])', r'_\1', text).lower()


def set_if_not_empty(sub_record, attrib, value):
    if value is not None and value != '':
        sub_record[attrib] = value


def append_if_not_empty(sub_record, attrib, value):
    if value is not None and value != '':
        sub_record[attrib].append(value)


def append(sub_record, attrib, value):
    sub_record[attrib].append(value or '')


def set_last_if_not_empty(sub_record, attrib, value):
    if value is not None and value != '':
        sub_record[attrib][-1] = value


def tri_bool(value):
    return value == 'true' if value else None


class FieldSetProcessor(object):

    def __init__(self, field, record, counter):
        self.field = field
        self.record = record
        self.counter = counter

    def run(self):
        tag = strip_namespace(self.field.tag)
        display_field = self.field.find('vra4:display', NAMESPACES)
        if display_field is not None:
            set_if_not_empty(self.record[tag][None], 'value', get_text(display_field))
            self.set_vra_attributes(display_field, self.record[tag][None])

        notes_field = self.field.find('vra4:notes', NAMESPACES)
        if notes_field is not None:
            set_if_not_empty(self.record[f'{tag[:-3]}-notes'][None], 'value', get_text(notes_field))
            self.set_vra_attributes(notes_field, self.record[f'{tag[:-3]}-notes'][None])

        base_tag = tag[:-3]
        for element in self.field.findall(f'vra4:{base_tag}', NAMESPACES):
            group = next(self.counter)
            self.set_vra_attributes(element, self.record[base_tag][group])
            getattr(self, snake_case(f'process_{base_tag}'))(element, group)

    def process_agent(self, field, group):
        date_field = None
        for element in field.iter():
            tag = strip_namespace(element.tag)
            if tag in ('attribution', 'culture', 'role'):
                append_if_not_empty(self.record[f'agent-{tag}'][group], 'value', get_text(element))
                self.append_vra_attributes(element, self.record[f'agent-{tag}'][group])
            elif tag == 'dates':
                date_field = self.record[f'agent-{tag}'][group]
                date_field['type'].append(element.attrib.get('type'))
                for t in ('earliest_date', 'latest_date'):
                    for s in ('', '_circa'):
                        date_field[t + s].append(None)
                self.append_vra_attributes(element, date_field)
            elif tag == 'name':
                append_if_not_empty(self.record[f'agent-{tag}'][group], 'value', get_text(element))
                self.append_vra_attributes(element, self.record[f'agent-{tag}'][group])
            elif tag in ('earliestDate', 'latestDate'):
                tag_snake_case = snake_case(tag)
                set_last_if_not_empty(date_field, tag_snake_case, get_text(element))
                set_last_if_not_empty(date_field, f'{tag_snake_case}_circa', tri_bool(element.attrib.get('circa')))

    def process_cultural_context(self, field, group):
        self.record['culturalContext'][group]['value'] = get_text(field)

    def process_date(self, field, group):
        date_field = self.record[f'date'][group]
        set_if_not_empty(date_field, 'type', field.attrib.get('type'))
        for element in field:
            tag_snake_case = snake_case(strip_namespace(element.tag))
            set_if_not_empty(date_field, tag_snake_case, get_text(element))
            set_if_not_empty(date_field, f'{tag_snake_case}_circa', tri_bool(element.attrib.get('circa')))

    def process_description(self, field, group):
        self.record['description'][group]['value'] = get_text(field)

    def process_inscription(self, field, group):
        self._process_basic_subelements(field, self.record, group)

    def process_location(self, field, group):
        set_if_not_empty(self.record['location'][group], 'type', field.attrib.get('type'))
        self._process_basic_subelements(field, self.record, group, extra_attrs=('type',))

    def process_material(self, field, group):
        set_if_not_empty(self.record['material'][group], 'type', field.attrib.get('type'))
        self.record['material'][group]['value'] = get_text(field)

    def process_measurements(self, field, group):
        set_if_not_empty(self.record['measurements'][group], 'type', field.attrib.get('type'))
        set_if_not_empty(self.record['measurements'][group], 'unit', field.attrib.get('unit'))
        self.record['measurements'][group]['value'] = get_text(field)

    def process_relation(self, field, group):
        set_if_not_empty(self.record['relation'][group], 'type', field.attrib.get('type'))
        set_if_not_empty(self.record['relation'][group], 'relids', field.attrib.get('relids'))
        self.record['relation'][group]['value'] = get_text(field)

    def process_rights(self, field, group):
        set_if_not_empty(self.record['rights'][group], 'type', field.attrib.get('type'))
        self._process_basic_subelements(field, self.record, group)

    def process_source(self, field, group):
        self._process_basic_subelements(field, self.record, group, extra_attrs=('type',))

    def process_state_edition(self, field, group):
        for attr in ('type', 'num', 'count'):
            set_if_not_empty(self.record['stateEdition'][group], attr, field.attrib.get(attr))
        self._process_basic_subelements(field, self.record, group)

    def process_style_period(self, field, group):
        self.record['stylePeriod'][group]['value'] = get_text(field)

    def process_subject(self, field, group):
        self._process_basic_subelements(field, self.record, group, extra_attrs=('type',))

    def process_technique(self, field, group):
        self.record['technique'][group]['value'] = get_text(field)

    def process_textref(self, field, group):
        self._process_basic_subelements(field, self.record, group, extra_attrs=('type', 'name'))

    def process_title(self, field, group):
        self.record['title'][group]['value'] = get_text(field)
        set_if_not_empty(self.record['title'][group], 'type', field.attrib.get('type'))

    def process_worktype(self, field, group):
        self.record['worktype'][group]['value'] = get_text(field)

    def _process_basic_subelements(self, field, record, group, value=True, extra_attrs=(), vra_attrs=True):
        field_tag = strip_namespace(field.tag)
        for element in field:
            tag = strip_namespace(element.tag)
            if value:
                append(record[f'{field_tag}-{tag}'][group], 'value', get_text(element))
            for attr in extra_attrs:
                append(record[f'{field_tag}-{tag}'][group], attr, field.attrib.get(attr))
            if vra_attrs:
                self.append_vra_attributes(element, record[f'{field_tag}-{tag}'][group], True)

    @staticmethod
    def _process_vra_attributes(field, callback, force):
        for attrib in VRA_ATTRIBUTES:
            if type(attrib) is tuple:
                attrib, map_to_attrib = attrib
            else:
                map_to_attrib = attrib
            if ':' in attrib:
                ns, attrib = attrib.split(':')
                attrib = f'{{{NAMESPACES[ns]}}}{attrib}'
            value = field.attrib.get(attrib)
            if attrib == 'pref' and value:
                value = value == 'true'
            if force or value is not None:
                callback(map_to_attrib, value)

    @staticmethod
    def set_vra_attributes(field, sub_record, force=False):
        def callback(attrib, value):
            sub_record[attrib] = value
        FieldSetProcessor._process_vra_attributes(field, callback, force)

    @staticmethod
    def append_vra_attributes(field, sub_record, force=False):
        def callback(attrib, value):
            sub_record[attrib].append(value)
        FieldSetProcessor._process_vra_attributes(field, callback, force)


def process(element, parent_collection=None, parent_work=None):
    tag = strip_namespace(element.tag)
    field_values = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    field_values[tag][None]['value'] = element.attrib.get('id')
    FieldSetProcessor.set_vra_attributes(element, field_values[tag][None])

    counter = count(1)
    child_records = []
    for child in element:
        child_tag = strip_namespace(child.tag)
        if child_tag in ('work', 'image'):
            child_records.append(child)
        else:
            FieldSetProcessor(child, field_values, counter).run()

    field_values = list(convert_to_field_values(field_values))

    record = dict()
    record['name'] = element.attrib.get('id')
    record['parent'] = parent_work or parent_collection
    record['manager'] = STANDARD_MANAGER
    record['identifier'] = next(
        fv['value'] for fv in field_values if fv['_field'] in ('image', 'work', 'collection'))

    yield record, field_values

    parent_collection = field_values if tag == 'collection' else parent_collection
    parent_work = field_values if tag == 'work' else parent_work

    for child_record in child_records:
        yield from process(child_record, parent_collection, parent_work)


def empty(result):
    return not result or not any(value for value in result.values())


def convert_to_field_values(record):
    order = count(100)
    for field_name in sorted(record.keys()):
        groups = record[field_name]
        for group in sorted(groups.keys()):
            attrs = groups[group]
            attr_keys = attrs.keys()
            attr_values = [values if type(values) is list else [values] for values in attrs.values()]
            for instance in zip(*attr_values):
                result = dict((k, v) for k, v in zip(attr_keys, instance) if v)
                if not empty(result):
                    result['group'] = group
                    result['_field'] = field_name
                    result['order'] = next(order) * 100
                    result['hidden'] = not field_name.endswith('Set')
                    yield result


def get_record(collection, identifier):
    identifier_field = standardfield('identifier')
    field_values = list(FieldValue.objects.select_related('record').filter(
        Q(field=identifier_field) | Q(field__in=identifier_field.equivalent.all()),
        value=identifier,
        index_value=identifier[:32],
        record__collection=collection,
    ))
    if len(field_values) == 0:
        return None
    elif len(field_values) == 1:
        record = field_values[0].record
        if record.manager != STANDARD_MANAGER:
            raise InvalidManager(f'Record "{identifier}" is not managed by {STANDARD_MANAGER}')
        return record
    raise Record.MultipleObjectsReturned(f'Found multiple records with identifier "{identifier}"')


def store(record, field_values, collection, replace):
    system_field = get_system_field()
    record.fieldvalue_set.filter(~Q(field=system_field), owner=None).delete()

    for values in field_values:
        field_name = values.pop('_field')
        try:
            field = Field.objects.get(name=field_name, standard__name=STANDARD)
        except Field.DoesNotExist:
            print(f'Could not find field "{field_name}"')
            raise
        VRACore4FieldValue.objects.create(record=record, field=field, **values)


class Command(BaseCommand):
    help = 'Command line VRA Core 4 XML import tool'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data', '-d', dest='data_file',
            required=True,
            help='VRA XML file'
        )
        parser.add_argument(
            '--collection', '-c', dest='collection',
            required=True,
            help='Collection identifier'
        )
        parser.add_argument(
            '--replace', '-r', dest='replace_records',
            action='store_true',
        )
        parser.add_argument(
            '--dryrun', '-n', dest='dryrun',
            action='store_true',
        )

    def handle(self, *args, **kwargs):

        data_file = kwargs.get('data_file')
        collection_id = int(kwargs.get('collection'))
        replace = kwargs.get('replace')
        dry_run = kwargs.get('dryrun')

        if dry_run:
            print('Dry run requested, not storing changes to database')

        collection = Collection.objects.get(id=collection_id)

        with open(data_file) as data:
            root = ElementTree.fromstring(data.read())

        xsd = xmlschema.XMLSchema(
            os.path.join(os.path.dirname(__file__), '..', '..', 'schemas', 'vra.xsd'))

        xsd.validate(root)

        for child in root:
            for record_values, field_values in process(child):
                identifier = record_values['identifier']
                print(f'Retrieving record "{identifier}"...', end='')
                record = get_record(collection, identifier)
                print(' replacing...' if record else ' creating...', end='')
                if not dry_run:
                    if not record:
                        record = Record.objects.create(
                            name=record_values['name'],
                            manager=record_values['manager'],
                        )
                        CollectionItem.objects.create(record=record, collection=collection)
                        # TODO: set parent
                    store(record, field_values, collection, replace)
                print(' done')
