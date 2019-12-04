
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.forms.utils import ErrorList
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden, \
    HttpResponse
from django.shortcuts import render
import json as simplejson
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse
from .models import Record, Collection, FieldSet, FieldSetField, \
    CollectionItem, Field, FieldValue
from .forms import FieldSetChoiceField, get_collection_visibility_prefs_form
from .functions import set_collection_visibility_preferences, \
    apply_collection_visibility_preferences, collection_dump
from rooibos.access.functions import filter_by_access, \
    get_effective_permissions_and_restrictions
from rooibos.storage.models import Media, Storage
from rooibos.userprofile.views import load_settings, store_settings
from .spreadsheetimport import SpreadsheetImport
import os
import random
import string
from rooibos.util import safe_int
from rooibos.middleware import HistoryMiddleware
from .tasks import csvimport


@login_required
def record_delete(request, id, name):
    if request.method == 'POST':
        record = Record.get_or_404(id, request.user)
        if record.editable_by(request.user):
            record.delete()
            messages.add_message(
                request,
                messages.INFO,
                message="Record deleted successfully."
            )

            from rooibos.middleware import HistoryMiddleware
            return HttpResponseRedirect(HistoryMiddleware.go_back(
                request,
                to_before=reverse(
                    'data-record', kwargs=dict(id=id, name=name)),
                default=reverse('solr-search')
            ))

    return HttpResponseRedirect(
        reverse('data-record', kwargs=dict(id=id, name=name)))


def get_allowed_collections_for_personal_records(user, readable_collections):
    allowed = []
    for c in Collection.objects.filter(id__in=readable_collections):
        restrictions = get_effective_permissions_and_restrictions(user, c)[3]
        if not restrictions or \
                restrictions.get('personal', 'yes').lower() != 'no':
            allowed.append(c.id)
    return allowed


def record(request, id, name, contexttype=None, contextid=None,
           contextname=None, edit=False, customize=False, personal=False,
           copy=False, copyid=None, copyname=None):

    collections = apply_collection_visibility_preferences(
        request.user, Collection.objects.all())
    writable_collections = list(
        filter_by_access(request.user, collections, write=True)
        .values_list('id', flat=True)
    )
    readable_collections = list(
        filter_by_access(request.user, collections)
        .values_list('id', flat=True)
    )
    personal_collections = None
    can_edit = request.user.is_authenticated()
    can_manage = False

    if id and name:
        record = Record.get_or_404(id, request.user)
        can_edit = can_edit and record.editable_by(request.user)
        can_manage = record.manageable_by(request.user)
    else:
        if request.user.is_authenticated():
            if personal:
                personal_collections = \
                    get_allowed_collections_for_personal_records(
                        request.user, readable_collections)
            if writable_collections or (personal and personal_collections):
                record = Record()
                if personal:
                    record.owner = request.user
            else:
                raise Http404()
        else:
            raise Http404()

    if record.owner:
        if personal_collections is None:
            personal_collections = \
                get_allowed_collections_for_personal_records(
                    request.user, readable_collections)
        valid_collections = (
            set(personal_collections) | set(writable_collections))
    else:
        valid_collections = writable_collections

    context = None
    if contexttype and contextid:
        app_label, model = contexttype.split('.')
        model_class = get_object_or_404(
            ContentType, app_label=app_label, model=model).model_class()
        context = get_object_or_404(
            filter_by_access(request.user, model_class), id=contextid)

    media = Media.objects.select_related().filter(
        record=record,
        storage__in=filter_by_access(request.user, Storage)
    )

    # Can any media be downloaded?
    download_image = False

    # Only list media that is downloadable or editable
    for m in media:
        # Calculate permissions and store with object for later use in template
        m.downloadable_in_template = m.is_downloadable_by(request.user)
        m.editable_in_template = m.editable_by(request.user)
        download_image = download_image or \
            m.is_downloadable_by(request.user, original=False)

    media = [m for m in media if m.downloadable_in_template or m.editable_in_template]

    edit = edit and request.user.is_authenticated()

    copyrecord = Record.get_or_404(copyid, request.user) if copyid else None

    class FieldSetForm(forms.Form):
        fieldset = FieldSetChoiceField(
            user=request.user, default_label='Default' if not edit else None)

    fieldsetform = FieldSetForm(request.GET)
    if fieldsetform.is_valid():
        if fieldsetform.cleaned_data['fieldset']:
            fieldset = FieldSet.for_user(request.user).get(
                id=fieldsetform.cleaned_data['fieldset'])
        else:
            fieldset = None
    elif edit:
        default_fieldset_name = getattr(
            settings, 'RECORD_DEFAULT_FIELDSET', 'dc')
        # Creating new record, use DC fieldset by default
        fieldset = FieldSet.objects.get(name=default_fieldset_name)
    else:
        fieldset = None

    collection_items = collectionformset = None

    if edit:

        if not can_edit and not customize and not context:
            return HttpResponseRedirect(
                reverse('data-record', kwargs=dict(id=id, name=name)))

        def _field_choices():
            fsf = list(FieldSetField.objects
                       .select_related('fieldset', 'field')
                       .all()
                       .order_by('fieldset__name', 'order', 'field__label'))
            grouped = {}
            for f in fsf:
                grouped.setdefault(
                    (f.fieldset.title, f.fieldset.id), []).append(f.field)
            others = list(
                Field.objects.exclude(id__in=[f.field.id for f in fsf])
                .order_by('label').values_list('id', 'label')
            )
            choices = [('', '-' * 10)] + [
                (set[0], [(f.id, f.label) for f in fields])
                for set, fields in sorted(
                    iter(grouped.items()), key=lambda s: s[0][0]
                )
            ]
            if others:
                choices.append(('Others', others))
            return choices

        class FieldValueForm(forms.ModelForm):

            def __init__(self, *args, **kwargs):
                super(FieldValueForm, self).__init__(*args, **kwargs)

            def clean_field(self):
                return Field.objects.get(id=self.cleaned_data['field'])

            def clean_context_type(self):
                context = self.cleaned_data.get('context_type')
                if context:
                    context = ContentType.objects.get(id=context)
                return context

            def clean(self):
                cleaned_data = self.cleaned_data
                return cleaned_data

            field = forms.ChoiceField(choices=_field_choices())
            value = forms.CharField(widget=forms.Textarea, required=False)
            context_type = forms.IntegerField(
                widget=forms.HiddenInput, required=False)
            context_id = forms.IntegerField(
                widget=forms.HiddenInput, required=False)
            index_value = forms.CharField(
                widget=forms.HiddenInput, required=False)
            browse_value = forms.CharField(
                widget=forms.HiddenInput, required=False)

            class Meta:
                model = FieldValue
                fields = "__all__"

        class CollectionForm(forms.Form):
            id = forms.IntegerField(widget=forms.HiddenInput)
            title = forms.CharField(widget=DisplayOnlyTextWidget)
            member = forms.BooleanField(required=False)
            shared = forms.BooleanField(required=False)

        fieldvalues_readonly = []
        if customize or context:
            fieldvalues = record.get_fieldvalues(
                owner=request.user, context=context, hidden=True
            ).filter(owner=request.user)
        else:
            fieldvalues = record.get_fieldvalues(hidden=True)

        field_value_formset = modelformset_factory(
            FieldValue,
            form=FieldValueForm,
            fields=FieldValueForm.Meta.fields,
            can_delete=True,
            extra=3
        )

        collection_formset = formset_factory(CollectionForm, extra=0)

        if request.method == 'POST':
            formset = field_value_formset(
                request.POST, request.FILES, queryset=fieldvalues, prefix='fv')
            if not (customize or context):
                collectionformset = collection_formset(
                    request.POST, request.FILES, prefix='c')
            else:
                collectionformset = None
            if formset.is_valid() and (
                    customize or context or collectionformset.is_valid()):

                record.save()

                if not (customize or context):
                    collections = dict(
                        (c['id'], c)
                        for c in collectionformset.cleaned_data
                        if c['id'] in valid_collections
                    )
                    for item in record.collectionitem_set.filter(
                            collection__in=valid_collections):
                        if item.collection_id in collections:
                            if not collections[item.collection_id]['member']:
                                item.delete()
                            elif collections[item.collection_id]['shared'] == \
                                    item.hidden:
                                item.hidden = not item.hidden
                                item.save()
                            del collections[item.collection_id]
                    for coll in list(collections.values()):
                        if coll['member']:
                            CollectionItem.objects.create(
                                record=record,
                                collection_id=coll['id'],
                                hidden=not coll['shared']
                            )

                instances = formset.save(commit=False)
                # Explicitly remove deleted objects
                for instance in formset.deleted_objects:
                    instance.delete()
                o1 = fieldvalues and max(v.order or 0 for v in fieldvalues) or 0
                o2 = instances and max(v.order or 0 for v in instances) or 0
                order = max(o1, o2, 0)
                for instance in instances:
                    if not instance.value:
                        if instance.id:
                            instance.delete()
                        continue
                    instance.record = record
                    if instance.order == 0:
                        order += 1
                        instance.order = order
                    if customize or context:
                        instance.owner = request.user
                    if context:
                        instance.context = context
                    instance.save()

                messages.add_message(
                    request,
                    messages.INFO,
                    message="Record saved successfully."
                )

                url = reverse(
                    'data-record-edit-customize' if customize
                    else 'data-record-edit',
                    kwargs=dict(id=record.id, name=record.name)
                )

                next = request.GET.get(
                    'next',
                    reverse(
                        'data-record',
                        kwargs=dict(id=record.id, name=record.name)
                    )
                )

                return HttpResponseRedirect(
                    url if 'save_and_continue' in request.POST else next)
        else:

            if copyrecord:
                initial = []
                for fv in copyrecord.get_fieldvalues(hidden=True):
                    initial.append(dict(
                        label=fv.label,
                        field=fv.field_id,
                        refinement=fv.refinement,
                        value=fv.value,
                        date_start=fv.date_start,
                        date_end=fv.date_end,
                        numeric_value=fv.numeric_value,
                        language=fv.language,
                        order=fv.order,
                        group=fv.group,
                        hidden=fv.hidden,
                    ))
                field_value_formset.extra = len(initial) + 3
            elif fieldset:
                needed = fieldset.fields.filter(
                    ~Q(id__in=[fv.field_id for fv in fieldvalues])
                ).order_by('fieldsetfield__order').values_list('id', flat=True)
                initial = [{'field': id2} for id2 in needed]
                field_value_formset.extra = len(needed) + 3
            else:
                initial = []

            formset = field_value_formset(
                queryset=fieldvalues, prefix='fv', initial=initial)
            if not (customize or context):

                collections = dict(
                    (
                        (coll.id, dict(id=coll.id, title=coll.title))
                        for coll in Collection.objects.filter(
                            id__in=valid_collections)
                    )
                )

                for item in (copyrecord or record).collectionitem_set.all():
                    collections.get(item.collection_id, {}).update(dict(
                        member=True,
                        shared=not item.hidden,
                    ))

                collections = list(collections.values())

                collectionformset = collection_formset(
                    prefix='c', initial=collections)

        part_of_works = None
        related_works = None

    else:
        fieldvalues_readonly = record.get_fieldvalues(
            owner=request.user, fieldset=fieldset)
        formset = None
        if record.owner == request.user or request.user.is_superuser:
            q = Q()
        else:
            q = Q(hidden=False)
        collection_items = record.collectionitem_set.filter(
            q, collection__in=readable_collections)

        part_of_works = []
        related_works = []

        works = FieldValue.objects.filter(
            record=record,
            field__name='relation',
            field__standard__prefix='dc',
            owner=None,
        ).values_list('value', 'refinement')

        for work, refinement in works:
            if refinement and refinement.lower() == 'ispartof':
                part_of_works.append(work)
            elif not refinement:
                related_works.append(work)

    if can_edit:
        from rooibos.storage.views import media_upload_form
        upload_file_form = media_upload_form(request)
        upload_form = upload_file_form() if upload_file_form else None
    else:
        upload_form = None

    record_usage = record.presentationitem_set.values('presentation') \
        .distinct().count() if can_edit else 0

    back_url = HistoryMiddleware.go_back(
        request,
        to_before=reverse('data-record-back-helper-url'),
    )

    if record.id:
        upload_url = (
            "%s?sidebar&next=%s" % (
                reverse('storage-media-upload', args=(record.id, record.name)),
                request.get_full_path() + '?refreshthumb=1'
            )
        )
    else:
        upload_url = None

    # In edit mode, optionally hide fieldset dropdown
    if formset and getattr(settings, 'HIDE_RECORD_FIELDSETS', False):
        fieldsetform = None

    return render(request,
        'data_record.html',
        {
            'record': record,
            'media': media,
            'fieldsetform': fieldsetform,
            'fieldset': fieldset,
            'fieldvalues': fieldvalues_readonly,
            'context': context,
            'customize': customize,
            'fv_formset': formset,
            'c_formset': collectionformset,
            'can_edit': can_edit,
            'can_manage': can_manage,
            'next': request.GET.get('next'),
            'collection_items': collection_items,
            'upload_form': upload_form,
            'upload_url': upload_url,
            'record_usage': record_usage,
            'back_url': back_url,
            'download_image': download_image,
            'part_of_works': part_of_works,
            'related_works': related_works,
        }
    )


def _get_scratch_dir():
    path = os.path.join(settings.SCRATCH_DIR, 'data-import')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def _get_filename(request, file):
    return request.COOKIES[settings.SESSION_COOKIE_NAME] + '-' + file


@login_required
def data_import(request):

    class UploadFileForm(forms.Form):
        file = forms.FileField()

        def clean_file(self):
            file = self.cleaned_data['file']
            if os.path.splitext(file.name)[1].lower() not in ('.csv', '.txt'):
                raise forms.ValidationError(
                    "Please upload a CSV file with a .csv file extension")
            return file

    utf8_error = False

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']

            filename = "".join(
                random.sample(string.ascii_lowercase + string.digits, 32))
            full_path = os.path.join(
                _get_scratch_dir(), _get_filename(request, filename))
            dest = open(full_path, 'wb+')
            for chunk in file.chunks():
                dest.write(chunk)
            dest.close()

            file = open(full_path, 'r', encoding='utf8', errors='strict')
            try:
                for line in file:
                    pass
                return HttpResponseRedirect(
                    reverse('data-import-file', args=(filename,)))
            except ValueError:
                utf8_error = True
            finally:
                file.close()

    else:
        form = UploadFileForm()

    return render(request,
        'data_import.html',
        {
            'form': form,
            'utf8_error': utf8_error,
        }
    )


class DisplayOnlyTextWidget(forms.HiddenInput):
    def render(self, name, value, attrs):
        r = super(DisplayOnlyTextWidget, self).render(name, value, attrs)
        r += mark_safe(
            conditional_escape(getattr(self, 'initial', value or '')))
        return r


@login_required
def data_import_file(request, file):

    available_collections = filter_by_access(request.user, Collection)
    writable_collection_ids = list(
        filter_by_access(request.user, Collection, write=True)
        .values_list('id', flat=True)
    )
    if not available_collections:
        raise Http404
    available_fieldsets = FieldSet.for_user(request.user)

    def _get_fields():
        return Field.objects.select_related('standard').all() \
            .order_by('standard', 'name')

    def _get_display_label(field):
        return '%s (%s) [%d]' % (field.label, field.name, field.id)

    def _field_choices():
        fsf = list(
            FieldSetField.objects.select_related('fieldset', 'field')
            .exclude(fieldset__name__startswith='browse-collection-')
            .exclude(fieldset__name='facet-fields')
            .order_by('fieldset__name', 'order', 'field__label')
        )
        grouped = {}
        for f in fsf:
            grouped.setdefault(
                (f.fieldset.title, f.fieldset.id), []).append(f.field)
        others = list(
            (field.id, _get_display_label(field))
            for field in
            Field.objects.exclude(
                id__in=[f.field.id for f in fsf]
            ).order_by('label')
        )
        choices = [
            ('', '-' * 10)
        ] + [
            (set[0], [(f.id, _get_display_label(f)) for f in fields])
            for set, fields
            in sorted(iter(grouped.items()), key=lambda s: s[0][0])
        ]

        if others:
            choices.append(('Others', others))
        return choices

    class ImportOptionsForm(forms.Form):
        separator = forms.CharField(required=False)
        collections = forms.MultipleChoiceField(
            choices=(
                (
                    c.id,
                    '%s%s' % (
                        '*' if c.id in writable_collection_ids else '',
                        c.title
                    )
                )
                for c in available_collections
            ),
            widget=forms.CheckboxSelectMultiple
        )
        fieldset = FieldSetChoiceField(user=request.user, default_label='any')
        update = forms.BooleanField(
            label='Update existing records', initial=True, required=False)
        add = forms.BooleanField(
            label='Add new records', initial=True, required=False)
        test = forms.BooleanField(
            label='Test import only', initial=False, required=False)
        personal = forms.BooleanField(
            label='Personal records', initial=False, required=False)

        def clean(self):
            cleaned_data = self.cleaned_data
            if any(self.errors):
                return cleaned_data
            personal = cleaned_data['personal']
            if not personal:
                for c in map(int, cleaned_data['collections']):
                    if c not in writable_collection_ids:
                        self._errors['collections'] = ErrorList(
                            ["Can only add personal records to "
                             "selected collections"])
                        del cleaned_data['collections']
                        return cleaned_data
            return cleaned_data

    class MappingForm(forms.Form):
        fieldname = forms.CharField(
            widget=DisplayOnlyTextWidget, required=False)
        mapping = forms.ChoiceField(choices=_field_choices(), required=False)
        separate = forms.BooleanField(required=False)
        label = forms.CharField(required=False)
        hidden = forms.BooleanField(required=False)
        refinement = forms.CharField(required=False)

    class BaseMappingFormSet(forms.formsets.BaseFormSet):
        def clean(self):
            if any(self.errors):
                return
            _dcidentifier = Field.objects.get(
                name='identifier', standard__prefix='dc')
            _identifier_ids = list(
                _dcidentifier.get_equivalent_fields()
                .values_list('id', flat=True)
            ) + [_dcidentifier.id]
            for i in range(self.total_form_count()):
                m = self.forms[i].cleaned_data['mapping']
                if m and int(m) in _identifier_ids:
                    return
            raise forms.ValidationError("At least one field must be mapped " \
                "to an identifier field.")

    create_mapping_formset = formset_factory(
        MappingForm, extra=0, formset=BaseMappingFormSet, can_order=True)

    def analyze(collections=None, separator=None, separate_fields=None,
                fieldset=None):
        try:
            infile = os.path.join(
                _get_scratch_dir(),
                _get_filename(request, file)
            )
            with open(infile, 'rU') as csvfile:
                imp = SpreadsheetImport(
                    csvfile,
                    collections,
                    separator=separator,
                    separate_fields=separate_fields,
                    preferred_fieldset=fieldset
                )
                return imp, imp.analyze()
        except IOError:
            raise Http404()

    if request.method == 'POST':
        form = ImportOptionsForm(request.POST)
        mapping_formset = create_mapping_formset(request.POST, prefix='m')
        if form.is_valid() and mapping_formset.is_valid():

            if int(form.cleaned_data.get('fieldset') or 0):
                fieldsets = available_fieldsets.get(
                    id=form.cleaned_data['fieldset'])
            else:
                fieldsets = None

            imp, preview_rows = analyze(
                available_collections.filter(
                    id__in=form.cleaned_data['collections']),
                form.cleaned_data['separator'],
                dict(
                    (f.cleaned_data['fieldname'], f.cleaned_data['separate'])
                    for f in mapping_formset.forms
                ),
                fieldsets
            )

            store_settings(
                request.user,
                'data_import_file_%s' % imp.field_hash,
                simplejson.dumps(
                    dict(
                        options=form.cleaned_data,
                        mapping=mapping_formset.cleaned_data)
                )
            )

            if request.POST.get('import_button'):

                arg = dict(
                    filename=_get_filename(request, file),
                    separator=form.cleaned_data['separator'],
                    collection_ids=list(map(
                        int, form.cleaned_data['collections'])),
                    update=form.cleaned_data['update'],
                    add=form.cleaned_data['add'],
                    test=form.cleaned_data['test'],
                    personal=form.cleaned_data['personal'],
                    mapping=dict(
                        (
                            f.cleaned_data['fieldname'],
                            int(f.cleaned_data['mapping'])
                        )
                        for f in mapping_formset.forms
                        if f.cleaned_data['mapping']
                    ),
                    separate_fields=dict(
                        (
                            f.cleaned_data['fieldname'],
                            f.cleaned_data['separate']
                        )
                        for f in mapping_formset.forms
                    ),
                    labels=dict(
                        (f.cleaned_data['fieldname'], f.cleaned_data['label'])
                        for f in mapping_formset.forms
                    ),
                    order=dict(
                        (
                            f.cleaned_data['fieldname'],
                            safe_int(f.cleaned_data['ORDER'], 0)
                        )
                        for f in mapping_formset.forms
                    ),
                    hidden=dict(
                        (f.cleaned_data['fieldname'], f.cleaned_data['hidden'])
                        for f in mapping_formset.forms
                    ),
                    refinements=dict(
                        (
                            f.cleaned_data['fieldname'],
                            f.cleaned_data['refinement']
                        )
                        for f in mapping_formset.forms
                    ),

                )

                task = csvimport.delay(owner=request.user.id, **arg)

                messages.add_message(
                    request,
                    messages.INFO,
                    message='Import job has been submitted.'
                )
                return HttpResponseRedirect(
                    "%s?highlight=%s" % (reverse('workers-jobs'), task.id))
        else:
            imp, preview_rows = analyze()
    else:
        imp, preview_rows = analyze()

        # try to load previously stored settings
        key = 'data_import_file_%s' % imp.field_hash
        values = load_settings(request.user, key)
        if key in values:
            value = simplejson.loads(values[key][0])
            mapping = value['mapping']
            options = value['options']
        else:
            mapping = [
                dict(fieldname=f, mapping=v.id if v else 0, separate=True)
                for f, v in imp.mapping.items()
            ]
            options = None

        mapping = sorted(mapping, key=lambda m: m['fieldname'])

        mapping_formset = create_mapping_formset(initial=mapping, prefix='m')
        form = ImportOptionsForm(initial=options)

    return render(request,
        'data_import_file.html',
        {
            'form': form,
            'preview_rows': preview_rows,
            'mapping_formset': mapping_formset,
            'writable_collections': bool(writable_collection_ids),
        }
    )


def record_preview(request, id):
    record = Record.get_or_404(id, request.user)
    return render(request,
        'data_previewrecord.html',
        {
            'record': record,
            'none': None,
        }
    )


@login_required
def manage_collections(request):

    collections = filter_by_access(request.user, Collection, manage=True)

    return render(request,
        'data_manage_collections.html',
        {
            'collections': collections,
        }
    )


@login_required
def manage_collection(request, id=None, name=None):

    if id and name:
        collection = get_object_or_404(
            filter_by_access(request.user, Collection, manage=True),
            id=id
        )
    elif request.user.has_perm('data.add_collection'):
        collection = Collection(title='Untitled')
        if not request.user.is_superuser:
            collection.owner = request.user
            collection.hidden = True
    else:
        raise Http404()

    class CollectionForm(forms.ModelForm):

        class UserField(forms.CharField):

            widget = forms.TextInput(attrs={'class': 'autocomplete-user'})

            def prepare_value(self, value):
                try:
                    if not value or getattr(self, "_invalid_user", False):
                        return value
                    return User.objects.get(id=value).username
                except ValueError:
                    return value
                except ObjectDoesNotExist:
                    return None

            def to_python(self, value):
                try:
                    return User.objects.get(username=value) if value else None
                except ObjectDoesNotExist:
                    self._invalid_user = True
                    raise ValidationError('User not found')

        children = forms.ModelMultipleChoiceField(
            queryset=filter_by_access(
                request.user, Collection).exclude(id=collection.id),
            widget=forms.CheckboxSelectMultiple,
            required=False
        )
        owner = UserField(
            widget=None if request.user.is_superuser else forms.HiddenInput,
            required=False
        )

        def clean_owner(self):
            if not request.user.is_superuser:
                # non-admins cannot change collection owner
                return collection.owner
            else:
                return self.cleaned_data['owner']

        class Meta:
            model = Collection
            fields = (
                'title', 'hidden', 'owner', 'description', 'agreement',
                'children', 'order'
            )

    if request.method == "POST":
        if request.POST.get('delete-collection'):
            if not (
                    request.user.is_superuser or
                    request.user == collection.owner):
                raise HttpResponseForbidden()
            messages.add_message(
                request,
                messages.INFO,
                message="Collection '%s' has been deleted." % collection.title
            )
            collection.delete()
            return HttpResponseRedirect(reverse('data-collections-manage'))
        else:
            form = CollectionForm(request.POST, instance=collection)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(
                    reverse(
                        'data-collection-manage',
                        kwargs=dict(
                            id=form.instance.id,
                            name=form.instance.name
                        )
                    )
                )
    else:
        form = CollectionForm(instance=collection)

    return render(request,
        'data_collection_edit.html',
        {
            'form': form,
            'collection': collection,
            'can_delete': collection.id and (
                request.user.is_superuser or collection.owner == request.user
            ),
        }
    )


@require_POST
@login_required
def save_collection_visibility_preferences(request):
    form = get_collection_visibility_prefs_form(request.user)(request.POST)

    if form.is_valid():
        if set_collection_visibility_preferences(
                request.user,
                form.cleaned_data['show_or_hide'],
                form.cleaned_data['collections']):
            messages.add_message(
                request,
                messages.INFO,
                message="Collection visibility preferences saved."
            )

    next = request.GET.get('next', reverse('main'))
    return HttpResponseRedirect(next)


def collection_dump_view(request, identifier, name):
    response = HttpResponse(content_type='text/plain')
    collection_dump(
        request.user,
        identifier,
        stream=response,
        prefix=request.GET.get('prefix')
    )
    return response
