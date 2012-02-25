#from rooibos.viewers import get_viewers
from __future__ import with_statement
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.forms.util import ErrorList
from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from models import *
from forms import FieldSetChoiceField
from rooibos.access import filter_by_access, check_access
from rooibos.presentation.models import Presentation
from rooibos.storage.models import Media, Storage
from rooibos.userprofile.views import load_settings, store_settings
from rooibos.util import json_view
from rooibos.workers.models import JobInfo
from spreadsheetimport import SpreadsheetImport
import os
import random
import string


def collections(request):
    collections = filter_by_access(request.user, Collection)
    return render_to_response('data_groups.html',
                              {'groups': collections, },
                              context_instance=RequestContext(request))

#def collection_raw(request, id, name):
#    collection = get_object_or_404(filter_by_access(request.user, Collection), id=id)
##    viewers = map(lambda v: v().generate(collection), get_viewers('collection', 'link'))
#    return render_to_response('data_group.html',
#                              {'collection': collection,
##                               'viewers': viewers,
#                               },
#                              context_instance=RequestContext(request))



@login_required
def record_delete(request, id, name):
    if request.method == 'POST':
        record = Record.get_or_404(id, request.user)
        if record.editable_by(request.user):
            record.delete()
            request.user.message_set.create(message="Record deleted successfully.")

            from rooibos.middleware import HistoryMiddleware
            return HttpResponseRedirect(HistoryMiddleware.go_back(
                request,
                to_before=reverse('data-record', kwargs=dict(id=id, name=name)),
                default=reverse('solr-search')
            ))

    return HttpResponseRedirect(reverse('data-record', kwargs=dict(id=id, name=name)))


def record(request, id, name, contexttype=None, contextid=None, contextname=None,
           edit=False, customize=False, personal=False, copy=False,
           copyid=None, copyname=None):

    writable_collections = list(filter_by_access(request.user, Collection, write=True).values_list('id', flat=True))
    readable_collections = list(filter_by_access(request.user, Collection).values_list('id', flat=True))
    can_edit = request.user.is_authenticated()
    can_manage = False

    if id and name:
        record = Record.get_or_404(id, request.user)
        can_edit = can_edit and record.editable_by(request.user)
        can_manage = record.manageable_by(request.user)
    else:
        if request.user.is_authenticated() and (writable_collections or (personal and readable_collections)):
            record = Record()
            if personal:
                record.owner = request.user
        else:
            raise Http404()

    if record.owner:
        valid_collections = set(readable_collections) | set(writable_collections)
    else:
        valid_collections = writable_collections

    context = None
    if contexttype and contextid:
        app_label, model = contexttype.split('.')
        model_class = get_object_or_404(ContentType, app_label=app_label, model=model).model_class()
        context = get_object_or_404(filter_by_access(request.user, model_class), id=contextid)

    media = Media.objects.select_related().filter(record=record,
                                                  storage__in=filter_by_access(request.user, Storage))
    # Only list media that is downloadable or editable
    for m in media:
        # Calculate permissions and store with object for later use in template
        m.downloadable_in_template =  m.is_downloadable_by(request.user)
        m.editable_in_template = m.editable_by(request.user)
    media = filter(lambda m: m.downloadable_in_template or m.editable_in_template, media)

    edit = edit and request.user.is_authenticated()

    copyrecord = Record.get_or_404(copyid, request.user) if copyid else None

    class FieldSetForm(forms.Form):
        fieldset = FieldSetChoiceField(user=request.user, default_label='Default' if not edit else None)

    fieldsetform = FieldSetForm(request.GET)
    if fieldsetform.is_valid():
        fieldset = FieldSet.for_user(request.user).get(id=fieldsetform.cleaned_data['fieldset']) if fieldsetform.cleaned_data['fieldset'] else None
    elif id and name:
        fieldset = None
    else:
        # Creating new record, use DC fieldset by default
        fieldset = FieldSet.objects.get(name='dc')

    collection_items = collectionformset = None

    if edit:

        if not can_edit and not customize and not context:
            return HttpResponseRedirect(reverse('data-record', kwargs=dict(id=id, name=name)))

        def _field_choices():
            fsf = list(FieldSetField.objects.select_related('fieldset', 'field').all().order_by('fieldset__name', 'order', 'field__label'))
            grouped = {}
            for f in fsf:
                grouped.setdefault((f.fieldset.title, f.fieldset.id), []).append(f.field)
            others = list(Field.objects.exclude(id__in=[f.field.id for f in fsf]).order_by('label').values_list('id', 'label'))
            choices = [('', '-' * 10)] + [(set[0], [(f.id, f.label) for f in fields])
                for set, fields in sorted(grouped.iteritems(), key=lambda s: s[0][0])]
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
            context_type = forms.IntegerField(widget=forms.HiddenInput, required=False)
            context_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
            index_value = forms.CharField(widget=forms.HiddenInput, required=False)

            class Meta:
                model = FieldValue
                exclude = []


        class CollectionForm(forms.Form):

            id = forms.IntegerField(widget=forms.HiddenInput)
            title = forms.CharField(widget=DisplayOnlyTextWidget)
            member = forms.BooleanField(required=False)
            shared = forms.BooleanField(required=False)


        fieldvalues_readonly = []
        if customize or context:
            fieldvalues = record.get_fieldvalues(owner=request.user, context=context, hidden=True).filter(owner=request.user)
        else:
            fieldvalues = record.get_fieldvalues(hidden=True)

        FieldValueFormSet = modelformset_factory(FieldValue, form=FieldValueForm,
                                                 exclude=FieldValueForm.Meta.exclude, can_delete=True, extra=3)

        CollectionFormSet = formset_factory(CollectionForm, extra=0)


        if request.method == 'POST':
            formset = FieldValueFormSet(request.POST, request.FILES, queryset=fieldvalues, prefix='fv')
            collectionformset = CollectionFormSet(request.POST, request.FILES, prefix='c') if not (customize or context) else None
            if formset.is_valid() and (customize or context or collectionformset.is_valid()):# or metadataform.is_valid()):

                record.save()

                if not (customize or context):
                    collections = dict((c['id'],c)
                        for c in collectionformset.cleaned_data
                        if c['id'] in valid_collections)
                    for item in record.collectionitem_set.filter(collection__in=valid_collections):
                        if collections.has_key(item.collection_id):
                            if not collections[item.collection_id]['member']:
                                item.delete()
                            elif collections[item.collection_id]['shared'] == item.hidden:
                                item.hidden = not item.hidden
                                item.save()
                            del collections[item.collection_id]
                    for coll in collections.values():
                        if coll['member']:
                            CollectionItem.objects.create(record=record,
                                                          collection_id=coll['id'],
                                                          hidden=not coll['shared'])

                instances = formset.save(commit=False)
                o1 = fieldvalues and max(v.order for v in fieldvalues) or 0
                o2 = instances and max(v.order for v in instances) or 0
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
                request.user.message_set.create(message="Record saved successfully.")

                url = reverse('data-record-edit-customize' if customize else 'data-record-edit',
                              kwargs=dict(id=record.id, name=record.name))

                next = request.GET.get('next',
                       reverse('data-record', kwargs=dict(id=record.id, name=record.name)))

                return HttpResponseRedirect(url if request.POST.has_key('save_and_continue') else next)
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
                FieldValueFormSet.extra = len(initial) + 3
            elif fieldset:
                needed = fieldset.fields.filter(~Q(id__in=[fv.field_id for fv in fieldvalues])).order_by('fieldsetfield__order').values_list('id', flat=True)
                initial = [{}] * len(fieldvalues) + [{'field': id} for id in needed]
                FieldValueFormSet.extra = len(needed) + 3
            else:
                initial = []

            formset = FieldValueFormSet(queryset=fieldvalues, prefix='fv', initial=initial)
            if not (customize or context):

                collections = dict(
                    ((coll.id, dict(id=coll.id, title=coll.title))
                        for coll in Collection.objects.filter(id__in=valid_collections)
                    )
                )

                for item in (copyrecord or record).collectionitem_set.all():
                    collections.get(item.collection_id, {}).update(dict(
                        member=True,
                        shared=not item.hidden,
                    ))

                collections = sorted(collections.values(), key=lambda c: c['title'])

                collectionformset = CollectionFormSet(prefix='c', initial=collections)

    else:
        fieldvalues_readonly = record.get_fieldvalues(owner=request.user, fieldset=fieldset)
        formset = None
        q = Q() if record.owner == request.user or request.user.is_superuser else Q(hidden=False)
        collection_items = record.collectionitem_set.filter(q, collection__in=readable_collections)

    if can_edit:
        from rooibos.storage.views import media_upload_form
        UploadFileForm = media_upload_form(request)
        upload_form = UploadFileForm() if UploadFileForm else None
    else:
        upload_form = None

    record_usage = record.presentationitem_set.values('presentation') \
                    .distinct().count() if can_edit else 0

    return render_to_response('data_record.html',
                              {'record': record,
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
                               'upload_url': ("%s?sidebar&next=%s" % (reverse('storage-media-upload', args=(record.id, record.name)), request.get_full_path()))
                                             if record.id else None,
                               'record_usage': record_usage,
                               },
                              context_instance=RequestContext(request))


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
            if os.path.splitext(file.name)[1] != '.csv':
                raise forms.ValidationError("Please upload a CSV file with a .csv file extension")
            return file

    utf8_error = False

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']

            filename = "".join(random.sample(string.letters + string.digits, 32))
            full_path = os.path.join(_get_scratch_dir(), _get_filename(request, filename))
            dest = open(full_path, 'wb+')
            for chunk in file.chunks():
                dest.write(chunk)
            dest.close()

            file = open(full_path, 'r')
            try:
                for line in file:
                    value = unicode(line, 'utf8')
                return HttpResponseRedirect(reverse('data-import-file', args=(filename,)))
            except UnicodeDecodeError:
                utf8_error = True
            finally:
                file.close()

    else:
        form = UploadFileForm()

    return render_to_response('data_import.html',
                              {'form': form,
                               'utf8_error': utf8_error,
                              },
                              context_instance=RequestContext(request))


class DisplayOnlyTextWidget(forms.HiddenInput):
    def render(self, name, value, attrs):
        return super(DisplayOnlyTextWidget, self).render(name, value, attrs) + \
            mark_safe(conditional_escape(getattr(self, 'initial', value or u'')))


@login_required
def data_import_file(request, file):

    available_collections = filter_by_access(request.user, Collection)
    writable_collection_ids = list(filter_by_access(request.user, Collection, write=True).values_list('id', flat=True))
    if not available_collections:
        raise Http404
    available_fieldsets = FieldSet.for_user(request.user)

    def _get_fields():
        return Field.objects.select_related('standard').all().order_by('standard', 'name')

    def _field_choices():
        fsf = list(FieldSetField.objects.select_related('fieldset', 'field').all().order_by('fieldset__name', 'order', 'field__label'))
        grouped = {}
        for f in fsf:
            grouped.setdefault((f.fieldset.title, f.fieldset.id), []).append(f.field)
        others = list(Field.objects.exclude(id__in=[f.field.id for f in fsf]).order_by('label').values_list('id', 'label'))
        choices = [('', '-' * 10)] + [(set[0], [(f.id, f.label) for f in fields])
            for set, fields in sorted(grouped.iteritems(), key=lambda s: s[0][0])]
        if others:
            choices.append(('Others', others))
        return choices


    #def _field_choices():
    #    grouped = {}
    #    for f in _get_fields():
    #        grouped.setdefault(f.standard and f.standard.title or 'Other', []).append(f)
    #    return [('0', '[do not import]'), ('-1', '[new field]')] + \
    #           [(g, [(f.id, f.label) for f in grouped[g]]) for g in grouped]

    class ImportOptionsForm(forms.Form):
        separator = forms.CharField(required=False)
        collections = forms.MultipleChoiceField(choices=((c.id, '%s%s' % ('*' if c.id in writable_collection_ids else '', c.title)) for c in sorted(available_collections, key=lambda c: c.title)),
                                                widget=forms.CheckboxSelectMultiple)
        fieldset = FieldSetChoiceField(user=request.user, default_label='any')
        #forms.ChoiceField(choices=[(0, 'any')] + [(f.id, f.title) for f in available_fieldsets], required=False)
        update = forms.BooleanField(label='Update existing records', initial=True, required=False)
        add = forms.BooleanField(label='Add new records', initial=True, required=False)
        test = forms.BooleanField(label='Test import only', initial=False, required=False)
        personal = forms.BooleanField(label='Personal records', initial=True, required=False)

        def clean(self):
            cleaned_data = self.cleaned_data
            if any(self.errors):
                return cleaned_data
            personal = cleaned_data['personal']
            if not personal:
                for c in map(int, cleaned_data['collections']):
                    if not c in writable_collection_ids:
                        self._errors['collections'] = ErrorList(["Can only add personal records to selected collections"])
                        del cleaned_data['collections']
                        return cleaned_data
            return cleaned_data

    class MappingForm(forms.Form):
        fieldname = forms.CharField(widget=DisplayOnlyTextWidget, required=False)
        mapping = forms.ChoiceField(choices=_field_choices(), required=False)
        separate = forms.BooleanField(required=False)
        label = forms.CharField(required=False)
        hidden = forms.BooleanField(required=False)

    class BaseMappingFormSet(forms.formsets.BaseFormSet):
        def clean(self):
            if any(self.errors):
                return
            _dcidentifier = Field.objects.get(name='identifier', standard__prefix='dc')
            _identifier_ids = list(_dcidentifier.get_equivalent_fields().values_list('id', flat=True)) + [_dcidentifier.id]
            for i in range(self.total_form_count()):
                if self.forms[i].cleaned_data['mapping'] and \
                    (int(self.forms[i].cleaned_data['mapping']) in _identifier_ids):
                    return
            raise forms.ValidationError, "At least one field must be mapped to an identifier field."


    MappingFormSet = formset_factory(MappingForm, extra=0, formset=BaseMappingFormSet, can_order=True)

    def analyze(collections=None, separator=None, separate_fields=None, fieldset=None):
        try:
            with open(os.path.join(_get_scratch_dir(), _get_filename(request, file)), 'rU') as csvfile:
                imp = SpreadsheetImport(csvfile, collections, separator=separator,
                                        separate_fields=separate_fields, preferred_fieldset=fieldset)
                return imp, imp.analyze()
        except IOError:
            raise Http404()

    if request.method == 'POST':
        form = ImportOptionsForm(request.POST)
        mapping_formset = MappingFormSet(request.POST, prefix='m')
        if form.is_valid() and mapping_formset.is_valid():

            imp, preview_rows = analyze(available_collections.filter(id__in=form.cleaned_data['collections']),
                       form.cleaned_data['separator'],
                       dict((f.cleaned_data['fieldname'], f.cleaned_data['separate'])
                            for f in mapping_formset.forms),
                       available_fieldsets.get(id=form.cleaned_data['fieldset']) if int(form.cleaned_data.get('fieldset') or 0) else None)

            store_settings(request.user,
                           'data_import_file_%s' % imp.field_hash,
                           simplejson.dumps(dict(options=form.cleaned_data, mapping=mapping_formset.cleaned_data)))

            if request.POST.get('import_button'):
                j = JobInfo.objects.create(owner=request.user,
                                       func='csvimport',
                                       arg=simplejson.dumps(dict(
                                                file=_get_filename(request, file),
                                                separator=form.cleaned_data['separator'],
                                                collections=map(int, form.cleaned_data['collections']),
                                                update=form.cleaned_data['update'],
                                                add=form.cleaned_data['add'],
                                                test=form.cleaned_data['test'],
                                                personal=form.cleaned_data['personal'],
                                                fieldset=form.cleaned_data['fieldset'],
                                                mapping=dict((f.cleaned_data['fieldname'], int(f.cleaned_data['mapping']))
                                                             for f in mapping_formset.forms if f.cleaned_data['mapping']),
                                                separate_fields=dict((f.cleaned_data['fieldname'], f.cleaned_data['separate'])
                                                                     for f in mapping_formset.forms),
                                                labels=dict((f.cleaned_data['fieldname'], f.cleaned_data['label'])
                                                             for f in mapping_formset.forms),
                                                order=dict((f.cleaned_data['fieldname'], int(f.cleaned_data['ORDER']))
                                                             for f in mapping_formset.forms),
                                                hidden=dict((f.cleaned_data['fieldname'], f.cleaned_data['hidden'])
                                                             for f in mapping_formset.forms),
                                                )
                                       ))
                j.run()
                request.user.message_set.create(message='Import job has been submitted.')
                return HttpResponseRedirect("%s?highlight=%s" % (reverse('workers-jobs'), j.id))
        else:
            imp, preview_rows = analyze()
    else:
        imp, preview_rows = analyze()

        # try to load previously stored settings
        key = 'data_import_file_%s' % imp.field_hash
        values = load_settings(request.user, key)
        if values.has_key(key):
            value = simplejson.loads(values[key][0])
            mapping = value['mapping']
            options = value['options']
        else:
            mapping = [dict(fieldname=f, mapping=v.id if v else 0, separate=True)
                       for f, v in imp.mapping.iteritems()]
            options = None

        mapping = sorted(mapping, key=lambda m: m['fieldname'])

        mapping_formset = MappingFormSet(initial=mapping, prefix='m')
        form = ImportOptionsForm(initial=options)

    return render_to_response('data_import_file.html',
                              {'form': form,
                               'preview_rows': preview_rows,
                               'mapping_formset': mapping_formset,
                               'writable_collections': bool(writable_collection_ids),
                              },
                              context_instance=RequestContext(request))


def record_preview(request, id):
    record = Record.get_or_404(id, request.user)
    return render_to_response('data_previewrecord.html',
                              {'record': record,
                               'none': None,
                               },
                              context_instance=RequestContext(request))

@login_required
def manage_collections(request):

    collections = filter_by_access(request.user, Collection, manage=True)

    return render_to_response('data_manage_collections.html',
                          {
                           'collections': collections,
                          },
                          context_instance=RequestContext(request))

@login_required
def manage_collection(request, id=None, name=None):

    if id and name:
        collection = get_object_or_404(filter_by_access(request.user, Collection, manage=True),
                                       id=id)
    else:
        collection = Collection(title='Untitled')
        if not request.user.is_superuser:
            collection.owner = request.user
            collection.hidden = True

    class CollectionForm(forms.ModelForm):

        class UserField(forms.CharField):

            widget=forms.TextInput(attrs={'class': 'autocomplete-user'})

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


        children = forms.ModelMultipleChoiceField(queryset=filter_by_access(request.user, Collection).exclude(id=collection.id),
                                                  widget=forms.CheckboxSelectMultiple,
                                                  required=False)
        owner = UserField(widget=None if request.user.is_superuser else forms.HiddenInput, required=False)

        def clean_owner(self):
            if not request.user.is_superuser:
                # non-admins cannot change collection owner
                return collection.owner
            else:
                return self.cleaned_data['owner']

        class Meta:
            model = Collection
            fields = ('title', 'hidden', 'owner', 'description', 'agreement', 'children')

    if request.method == "POST":
        if request.POST.get('delete-collection'):
            if not (request.user.is_superuser or request.user == collection.owner):
                raise HttpResponseForbidden()
            request.user.message_set.create(message="Collection '%s' has been deleted." % collection.title)
            collection.delete()
            return HttpResponseRedirect(reverse('data-collections-manage'))
        else:
            form = CollectionForm(request.POST, instance=collection)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('data-collection-manage', kwargs=dict(
                    id=form.instance.id, name=form.instance.name)))
    else:
        form = CollectionForm(instance=collection)

    return render_to_response('data_collection_edit.html',
                          {'form': form,
                           'collection': collection,
                           'can_delete': collection.id and (request.user.is_superuser or collection.owner == request.user),
                          },
                          context_instance=RequestContext(request))
