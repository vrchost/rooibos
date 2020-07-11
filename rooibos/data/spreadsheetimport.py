from django.db.models import Q, Count
from django.db import reset_queries
from django.contrib.auth.models import User
from .models import Field, FieldValue, Record, CollectionItem, get_system_field
import csv
import os


class CustomDictReader(csv.DictReader):

    @csv.DictReader.fieldnames.getter
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                self._fieldnames = [n.strip() for n in next(self.reader)]
            except StopIteration:
                pass
        self.line_num = self.reader.line_num
        return self._fieldnames


class SpreadsheetImport(object):

    events = [
        'on_added', 'on_added_skipped', 'on_updated', 'on_updated_skipped',
        'on_duplicate_in_file_skipped', 'on_no_id_skipped', 'on_owner_skipped',
        'on_duplicate_in_collection_skipped', 'on_continuation']

    def __init__(self, csv_file, collections, separator=';',
                 preferred_fieldset=None, owner=None, mapping=None,
                 separate_fields=None, labels=None, order=None,
                 hidden=None,
                 refinements=None,
                 **kwargs):
        self._fields = (
            preferred_fieldset.fields.select_related('standard').all()
            if preferred_fieldset
            else Field.objects.select_related('standard').all())
        self._dcidentifier = Field.objects.get(name='identifier',
                                               standard__prefix='dc')
        self._identifier_ids = list(
            self._dcidentifier.get_equivalent_fields().values_list(
                'id', flat=True)
        ) + [self._dcidentifier.id]
        self.csv_file = csv_file
        self.separator = separator
        self.analyzed = False
        self.field_hash = None
        if mapping:
            self.mapping = dict((k, self._get_field(v))
                                for k, v in mapping.items())
        else:
            self.mapping = dict()
        self.labels = labels or dict()
        self.order = order or dict()
        self.hidden = hidden or dict()
        self.refinements = refinements or dict()
        self.separate_fields = separate_fields or dict()
        self.owner = owner
        self.collections = collections
        for event in self.events:
            setattr(self, event, [kwargs[event]] if event in kwargs else [])
        self.decode_error = False

    def _get_field(self, field):
        """
        If field is an int, resolves to corresponding field,
        otherwise just returns field.
        """
        if type(field) == int:
            for f in self._fields:
                if f.id == field:
                    return f
            else:
                return None
        return field

    def _split_value(self, value, split=True):
        if not value:
            return None
        if (self.separator and split):
            return [s.strip() for s in value.split(self.separator)]
        else:
            return [value.strip()]

    def _split_values(self, row):
        return dict(
            (key, self._split_value(val, self.separate_fields.get(key)))
            for key, val in row.items()
            if key)

    def _get_reader(self):
        self.csv_file.seek(0)
        # skip BOM in some UTF-8 files
        start = 3 if (self.csv_file.read(3) == "\xef\xbb\xbf") else 0
        self.csv_file.seek(start)
        dialect = csv.Sniffer().sniff(self.csv_file.read(65536))
        dialect.delimiter = ','
        dialect.doublequote = True
        self.csv_file.seek(start)
        return CustomDictReader(self.csv_file, dialect=dialect)

    def _guess_mapping(self, field):
        scores = {}
        for standard_field in self._fields:
            if (field == standard_field.name or field == standard_field.label):
                # exact match with field name or label
                if standard_field.standard:
                    if standard_field.standard.prefix == 'dc':
                        # exact match with Dublin Core field, maximum score,
                        # return immediately
                        return standard_field
                    else:
                        # exact match with other standard field
                        score = 2
                else:
                    # exact match with non-standard field
                    score = 1
                if score not in scores:
                    scores[score] = standard_field

        return scores[max(scores.keys())] if scores else None

    def analyze(self, preview_rows=5, mapping=None, separate_fields=None):
        reader = self._get_reader()
        if mapping:
            self.mapping = mapping
        if separate_fields:
            self.separate_fields = separate_fields

        rows = [self._split_values(row)
                for i, row in zip(list(range(preview_rows)), reader)]
        if not rows:
            return None

        fields = [_f for _f in list(rows[0].keys()) if _f]
        self.field_hash = hash('\t'.join(sorted(fields)))
        if not self.mapping:
            self.mapping = dict((field, self._guess_mapping(field))
                                for field in fields)
        if not self.separate_fields:
            self.separate_fields = dict((field, True) for field in fields)

        self.analyzed = True
        return rows

    def get_identifier_field(self, mapping=None):
        if not mapping:
            mapping = self.mapping
        for field, mapped in mapping.items():
            if mapped and mapped.id in self._identifier_ids:
                return field
        return None

    def find_duplicate_identifiers(self):
        query = (FieldValue.objects.filter(
            record__collection__in=self.collections,
            field__in=self._identifier_ids)
            .values('value').annotate(c=Count('id')).exclude(c=1))
        identifiers = query.values_list('value', flat=True)
        return identifiers

    class NoIdentifierException(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    def run(self, update=True, add=True, test=False, target_collections=[],
            skip_rows=0):
        if not self.analyzed:
            self.analyze(preview_rows=1)

        identifier_field = self.get_identifier_field()
        if not identifier_field:
            raise SpreadsheetImport.NoIdentifierException(
                'No column is mapped to an identifier field')

        system_field = get_system_field()

        def apply_values(record, row, is_new=False):
            if not is_new:
                record.fieldvalue_set.filter(~Q(field=system_field),
                                             owner=None).delete()
            for field, values in row.items():
                target = self.mapping.get(field)
                if target and values:
                    for order, value in enumerate(values):
                        record.fieldvalue_set.create(
                            field=target,
                            value=value,
                            label=self.labels.get(field),
                            order=self.order.get(field, order),
                            hidden=self.hidden.get(field, False),
                            refinement=self.refinements.get(field))

        reader = self._get_reader()

        self.added = self.added_skipped = self.updated = \
            self.updated_skipped = self.duplicate_in_file_skipped = \
            self.no_id_skipped = self.owner_skipped = \
            self.duplicate_in_collection_skipped = 0
        self.processed_ids = dict()

        def process_row(row):
            ids = row[identifier_field]
            if '\n'.join(ids) in self.processed_ids:
                self.duplicate_in_file_skipped += 1
                for func in self.on_duplicate_in_file_skipped:
                    func(ids)
                return
            self.processed_ids['\n'.join(ids)] = None
            fvs = FieldValue.objects.select_related('record').filter(
                record__collection__in=self.collections,
                owner=None,
                field__in=self._identifier_ids,
                index_value__in=(x[:32] for x in ids),
                value__in=ids)
            if not fvs:
                if add:
                    # create new record
                    if not test:
                        record = Record.objects.create(owner=self.owner)
                        apply_values(record, row, is_new=True)
                        for collection in (
                                target_collections or self.collections):
                            CollectionItem.objects.get_or_create(
                                record=record,
                                collection=collection
                            )
                    self.added += 1
                    for func in self.on_added:
                        func(ids)
                else:
                    # adding new records is disabled
                    self.added_skipped += 1
                    for func in self.on_added_skipped:
                        func(ids)
            elif len(fvs) == 1:
                if fvs[0].record.owner == self.owner:
                    if update:
                        # update existing record
                        # (including records just created in previous row)
                        if not test:
                            record = fvs[0].record
                            apply_values(record, row)
                            for collection in (
                                    target_collections or self.collections):
                                CollectionItem.objects.get_or_create(
                                    record=record,
                                    collection=collection)
                        self.updated += 1
                        for func in self.on_updated:
                            func(ids)
                    else:
                        # updating records is disabled
                        self.updated_skipped += 1
                        for func in self.on_updated_skipped:
                            func(ids)
                else:
                    self.owner_skipped += 1
                    for func in self.on_owner_skipped:
                        func(ids)
            else:
                # duplicate id found
                self.duplicate_in_collection_skipped += 1
                for func in self.on_duplicate_in_collection_skipped:
                    func(ids)

        for skip in range(skip_rows):
            next(reader)

        last_row = None

        for i, row in enumerate(reader):

            reset_queries()

            row = self._split_values(row)
            if not last_row:
                last_row = row
                continue

            # compare IDs of current and last rows
            last_id = last_row.get(identifier_field)
            if not last_id:
                last_row = row
                self.no_id_skipped += 1
                for func in self.on_no_id_skipped:
                    func(None)
                continue

            current_id = row.get(identifier_field)

            if not current_id or (last_id == current_id):
                # combine current and last rows
                for key, values in row.items():
                    v = last_row.get(key) or []
                    for value in (values or []):
                        if value not in v:
                            v.append(value)
                    last_row[key] = v
                for func in self.on_continuation:
                    func(last_id)
            else:
                process_row(last_row)
                last_row = row

        if last_row:
            process_row(last_row)



def create_import_job(mapping_file, data_file, collections):
    fields = dict(
        (f.full_name, f) for f in Field.objects.all()
    )

    def get_field_id(field_name):
        f = fields.get(field_name)
        if not f:
            print("WARNING: Field %s not found" % field_name)
            return None
        return f.id

    def str2bool(value):
        return value.lower() in ("1", "true", "t", "yes", "y")

    mappings = []
    with open(mapping_file, 'rU') as mapping_fileobj:
        mapping = CustomDictReader(mapping_fileobj)
        for m in mapping:
            m['mapto'] = get_field_id(m['mapto'])
            mappings.append(m)

    mapping = dict(
        (m['field'], m['mapto']) for m in mappings
    )
    separate_fields = dict(
        (m['field'], str2bool(m['separate'])) for m in mappings
    )
    labels = dict(
        (m['field'], m['label']) for m in mappings
    )
    hidden = dict(
        (m['field'], str2bool(m['hidden'])) for m in mappings
    )
    order = dict(
        (m['field'], int(m['order'])) for m in mappings
    )
    refinements = dict(
        (m['field'], m['refinement']) for m in mappings
    )

    args = dict(
        filename=os.path.basename(data_file),
        separator=';',
        collection_ids=collections,
        update=True,
        add=True,
        test=False,
        personal=False,
        mapping=mapping,
        separate_fields=separate_fields,
        labels=labels,
        order=order,
        hidden=hidden,
        refinements=refinements,
    )

    from .tasks import csvimport
    signature = csvimport.si(
        owner=User.objects.get(username='admin').id, **args)
    return signature


def submit_import_job(mapping_file, data_file, collections):
    sig = create_import_job(mapping_file, data_file, collections)
    task = sig.delay()
    return task
