from django.db.models import Q
from models import Collection, Field, FieldValue, FieldSet, Record, CollectionItem
from xml.dom import minidom, Node
from decimal import Decimal

def read_core4(file):
    """
    Import from a VRA Core 4 XML file

    Unsupported:
    - count and num attributes of stateEdition element
    - any relations except a single imageOf relation to another record of the same batch
    """
    fields = dict((f.name, f) for f in Field.objects.filter(standard__prefix='vra'))
    dc_identifier = Field.objects.get(name='identifier', standard__prefix='dc')

    def elementNodes(nodes):
        return filter(lambda n: n.nodeType == Node.ELEMENT_NODE, nodes)

    def dot(*values):
        return '.'.join(filter(None, values))

    def process_date(element, field, counter, refinement=None, order=0):
        type = element.getAttribute('type')
        earliest = element.getElementsByTagName('earliestDate') or None
        latest = element.getElementsByTagName('latestDate') or None
        if earliest: earliest = earliest[0].firstChild and earliest[0].firstChild.nodeValue
        if latest: latest = latest[0].firstChild and latest[0].firstChild.nodeValue
        if earliest or latest:
            return [FieldValue(field=field, refinement=dot(refinement, type),
                               value='%s - %s' % (earliest, latest), hidden=True,
                               date_start=earliest, date_end=latest, group=counter, order=order)]
        return []

    def process_element(element, field, counter):
        type = element.getAttribute('type')
        children = elementNodes(element.childNodes)
        values = []
        order = 0
        if children:
            for e in children:
                value = e.firstChild and e.firstChild.nodeValue or None
                if value:
                    order += 1
                    values.append(FieldValue(field=field, refinement=dot(type, e.localName, e.getAttribute('type')),
                                             value=value, group=counter, order=order))
        else:
            value = element.firstChild and element.firstChild.nodeValue or None
            if value: value = value.strip()
            return value and [FieldValue(field=field, refinement=type, value=value, group=counter)] or []
        return values

    def process_element_agent(element, field, counter):
        values = []
        order = 0
        for e in elementNodes(element.childNodes):
            value = e.firstChild and e.firstChild.nodeValue or None
            if value:
                order += 1
                if e.localName == 'dates':
                    values.extend(process_date(e, field, counter, 'dates', order))
                elif e.localName == 'name':
                    values.append(FieldValue(field=field, refinement=dot('name', e.getAttribute('type')),
                                             value=value, group=counter, order=order))
                else:
                    values.append(FieldValue(field=field, refinement=e.localName,
                                             value=value, group=counter, order=order))
        return values

    def process_element_measurement(element, field, counter):
        value = element.firstChild and element.firstChild.nodeValue or None
        if value:
            try:
                numvalue = Decimal(value)
            except:
                numvalue = None
            return [FieldValue(field=field, refinement=element.getAttribute('type'),
                               value=value + element.getAttribute('unit'), numeric_value=numvalue, group=counter)]
        return []

    record_relations = []

    def process_element_relation(element, field, counter):
        relids = element.getAttribute('relids')
        refid = element.getAttribute('refid')
        type = element.getAttribute('type')
        if type == 'imageOf':
            record_relations.append((relids, refid))
        return process_element(element, field, counter)

    processors = dict((f, process_element) for f in fields.keys())
    processors['date'] = process_date
    processors['agent'] = process_element_agent
    processors['measurements'] = process_element_measurement
    processors['relation'] = process_element_relation

    def process_element_set(element_set):
        field = fields[element_set.localName[:-3].lower()]
        values = []
        for counter, element in enumerate(elementNodes(element_set.childNodes)):
            name = element.localName
            value = element.firstChild and element.firstChild.nodeValue or None
            if name == 'display':
                if value: values.append(FieldValue(field=field, value=value))
            elif name == 'notes':
                if value: values.append(FieldValue(field=field, refinement='notes', value=value))
            else:
                values.extend(processors[field.name](element, field, counter))
        return values

    def get_first_value(values, condition):
        filtered = filter(condition, values)
        return filtered and filtered[0].value or None

    def process_record(record):
        id = record.getAttribute('id')
        refid = record.getAttribute('refid')
        source = record.getAttribute('source')
        values = []
        del record_relations[:]
        for child in elementNodes(record.childNodes):
            values.extend(process_element_set(child))
        # TODO: find existing record to replace
        record = Record()
        record.name = get_first_value(values, lambda v: v.field.name == 'source' and
                                      v.refinement.startswith('refid')) \
                      or get_first_value(values, lambda v: v.field.name == 'title')
        record.save(force_insert=True)
        record.fieldvalue_set.add(*values)
        record.fieldvalue_set.create(field=dc_identifier, value=id)
        # Temporary properties to link records together
        record._core4_ids = (id, refid)
        record._core4_parent = record_relations and record_relations[0] or None
        return record

    dom = minidom.parse(file)
    if dom.documentElement.namespaceURI <> 'http://www.vraweb.org/vracore4.htm':
        raise Exception("File is not a valid VRA Core 4 file (invalid namespace)")
    records = map(process_record,
                  dom.documentElement.getElementsByTagName('work') + \
                  dom.documentElement.getElementsByTagName('image'))
    for record in filter(lambda r: r._core4_parent, records):
        parent = filter(lambda r: r._core4_ids[0] == record._core4_parent[0] or
                                  r._core4_ids[1] == record._core4_parent[1], records)
        if parent:
            record.parent = parent[0]
            record.save()

    return records

def test(collection):
    records = read_core4('d:/dev/rooibos/rooibos/data/testdata/MuseeSample.xml')
    for record in records:
        CollectionItem.objects.create(collection=collection, record=record)
