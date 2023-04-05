import os.path
import re
from collections import defaultdict
from itertools import count
from pprint import pprint
from xml.etree import ElementTree

import xmlschema
from django.core.management import BaseCommand

from rooibos.vracore4.models import STANDARD_NAMESPACE


NAMESPACES = {'vra4': STANDARD_NAMESPACE}

VRA_ATTRIBUTES = (
    'dataDate',
    'extent',
    'href',
    'xml:lang',
    'pref',
    'refid',
    'rules',
    'source',
    'vocab',
)


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


class Processors(object):

    @staticmethod
    def process_agent(field, record, group):
        date_field = None
        for element in field.iter():
            tag = strip_namespace(element.tag)
            if tag in ('attribution', 'culture', 'role'):
                append_if_not_empty(record[f'agent-{tag}'][group], 'value', get_text(element))
                Processors.append_vra_attributes(element, record[f'agent-{tag}'][group])
            elif tag == 'dates':
                date_field = record[f'agent-{tag}'][group]
                date_field['type'].append(element.attrib.get('type'))
                for t in ('earliest_date', 'latest_date'):
                    for s in ('', '_circa'):
                        date_field[t + s].append(None)
                Processors.append_vra_attributes(element, date_field)
            elif tag == 'name':
                append_if_not_empty(record[f'agent-{tag}'][group], 'value', get_text(element))
                Processors.append_vra_attributes(element, record[f'agent-{tag}'][group])
            elif tag in ('earliestDate', 'latestDate'):
                tag_snake_case = snake_case(tag)
                set_last_if_not_empty(date_field, tag_snake_case, get_text(element))
                set_last_if_not_empty(date_field, f'{tag_snake_case}_circa', tri_bool(element.attrib.get('circa')))

    @staticmethod
    def process_cultural_context(field, record, group):
        record['culturalContext'][group]['value'] = get_text(field)

    @staticmethod
    def process_date(field, record, group):
        date_field = record[f'date'][group]
        set_if_not_empty(date_field, 'type', field.attrib.get('type'))
        for element in field:
            tag_snake_case = snake_case(strip_namespace(element.tag))
            set_if_not_empty(date_field, tag_snake_case, get_text(element))
            set_if_not_empty(date_field, f'{tag_snake_case}_circa', tri_bool(element.attrib.get('circa')))

    @staticmethod
    def process_description(field, record, group):
        record['description'][group]['value'] = get_text(field)

    @staticmethod
    def process_inscription(field, record, group):
        Processors._process_basic_subelements(field, record, group)

    @staticmethod
    def process_location(field, record, group):
        set_if_not_empty(record['location'][group], 'type', field.attrib.get('type'))
        Processors._process_basic_subelements(field, record, group, extra_attrs=('type',))

    @staticmethod
    def process_material(field, record, group):
        set_if_not_empty(record['material'][group], 'type', field.attrib.get('type'))
        record['material'][group]['value'] = get_text(field)

    @staticmethod
    def process_measurements(field, record, group):
        set_if_not_empty(record['measurements'][group], 'type', field.attrib.get('type'))
        set_if_not_empty(record['measurements'][group], 'unit', field.attrib.get('unit'))
        record['measurements'][group]['value'] = get_text(field)

    @staticmethod
    def process_relation(field, record, group):
        set_if_not_empty(record['relation'][group], 'type', field.attrib.get('type'))
        set_if_not_empty(record['relation'][group], 'relids', field.attrib.get('relids'))
        record['relation'][group]['value'] = get_text(field)

    @staticmethod
    def process_rights(field, record, group):
        set_if_not_empty(record['rights'][group], 'type', field.attrib.get('type'))
        Processors._process_basic_subelements(field, record, group)

    @staticmethod
    def process_source(field, record, group):
        Processors._process_basic_subelements(field, record, group, extra_attrs=('type',))

    @staticmethod
    def process_state_edition(field, record, group):
        for attr in ('type', 'num', 'count'):
            set_if_not_empty(record['stateEdition'][group], attr, field.attrib.get(attr))
        Processors._process_basic_subelements(field, record, group)

    @staticmethod
    def process_style_period(field, record, group):
        record['stylePeriod'][group]['value'] = get_text(field)

    @staticmethod
    def process_subject(field, record, group):
        Processors._process_basic_subelements(field, record, group, extra_attrs=('type',))

    @staticmethod
    def process_technique(field, record, group):
        record['technique'][group]['value'] = get_text(field)

    @staticmethod
    def process_textref(field, record, group):
        Processors._process_basic_subelements(field, record, group, extra_attrs=('type', 'name'))

    @staticmethod
    def process_title(field, record, group):
        Processors._process_basic_subelements(field, record, group, extra_attrs=('type',))

    @staticmethod
    def process_worktype(field, record, group):
        record['worktype'][group]['value'] = get_text(field)

    @staticmethod
    def _process_basic_subelements(field, record, group, value=True, extra_attrs=(), vra_attrs=True):
        field_tag = strip_namespace(field.tag)
        for element in field:
            tag = strip_namespace(element.tag)
            if value:
                append(record[f'{field_tag}-{tag}'][group], 'value', get_text(element))
            for attr in extra_attrs:
                append(record[f'{field_tag}-{tag}'][group], attr, field.attrib.get(attr))
            if vra_attrs:
                Processors.append_vra_attributes(element, record[f'{field_tag}-{tag}'][group], True)

    @staticmethod
    def _process_vra_attributes(field, callback, force):
        for attrib in VRA_ATTRIBUTES:
            value = field.attrib.get(attrib)
            if attrib == 'pref' and value:
                value = value == 'true'
            if force or value is not None:
                callback(attrib, value)

    @staticmethod
    def set_vra_attributes(field, sub_record, force=False):
        def callback(attrib, value):
            sub_record[attrib] = value
        Processors._process_vra_attributes(field, callback, force)

    @staticmethod
    def append_vra_attributes(field, sub_record, force=False):
        def callback(attrib, value):
            sub_record[attrib].append(value)
        Processors._process_vra_attributes(field, callback, force)


def process_set(field, record, counter):
    tag = strip_namespace(field.tag)
    display_field = field.find('vra4:display', NAMESPACES)
    if display_field is not None:
        set_if_not_empty(record[tag], 'value', get_text(display_field))
        Processors.set_vra_attributes(display_field, record[tag])

    notes_field = field.find('vra4:notes', NAMESPACES)
    if notes_field is not None:
        set_if_not_empty(record[f'{tag[:-3]}-notes'], 'value', get_text(notes_field))
        Processors.set_vra_attributes(notes_field, record[f'{tag[:-3]}-notes'])

    base_tag = tag[:-3]
    for element in field.findall(f'vra4:{base_tag}', NAMESPACES):
        group = next(counter)
        Processors.set_vra_attributes(element, record[base_tag][group])
        getattr(Processors, snake_case(f'process_{base_tag}'))(element, record, group)


def process(element, parent_collection=None, parent_work=None):
    tag = strip_namespace(element.tag)
    record = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    record[tag]['value'] = element.attrib.get('id')
    Processors.set_vra_attributes(element, record[tag])

    # TODO: do something with parents

    counter = count(1)
    child_records = []
    for child in element:
        child_tag = strip_namespace(child.tag)
        if child_tag in ('work', 'image'):
            child_records.append(child)
        else:
            process_set(child, record, counter)

    pprint(record)

    parent_collection = record if tag == 'collection' else parent_collection
    parent_work = record if tag == 'work' else parent_work

    for child_record in child_records:
        process(child_record, parent_collection, parent_work)


class Command(BaseCommand):
    help = 'Command line VRA Core 4 XML import tool'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data', '-d', dest='data_file',
            help='VRA XML file'
        )
        parser.add_argument(
            '--collection', '-c', dest='collections',
            action='append',
            help='Collection identifier'
        )

    def handle(self, *args, **kwargs):

        data_file = kwargs.get('data_file')
        collections = list(map(int, kwargs.get('collections') or list()))

        if not data_file or not collections:
            print("--collection and --data are required parameters")
            return

        with open(data_file) as data:
            root = ElementTree.fromstring(data.read())

        xsd = xmlschema.XMLSchema(
            os.path.join(os.path.dirname(__file__), '..', '..', 'schemas', 'vra.xsd'))

        xsd.validate(root)

        for child in root:
            process(child)
