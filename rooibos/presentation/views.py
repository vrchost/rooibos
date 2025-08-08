import re

from django.contrib import messages
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory, ModelForm
from django.db.models.aggregates import Count
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db import connection
from django import forms
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from tagging.models import Tag, TaggedItem
from rooibos.util.models import OwnedWrapper
from rooibos.access.functions import filter_by_access
from rooibos.data.models import FieldSet, Record, title_from_fieldvalues, standardfield_ids
from rooibos.data.forms import FieldSetChoiceField
from rooibos.data.functions import get_fields_for_set
from rooibos.ui.actionbar import update_actionbar_tags
from rooibos.access.models import ExtendedGroup, AUTHENTICATED_GROUP, \
    AccessControl
from rooibos.userprofile.views import load_settings, store_settings
from rooibos.util import json_view, validate_next_link
from rooibos.util.markdown import markdown
from rooibos.storage.functions import get_image_for_record
from .models import Presentation, PresentationItem
from .functions import duplicate_presentation
import base64
import os
import logging
from PIL import Image

from ..solr.views import search
from ..viewers import get_viewers_for_object


logger = logging.getLogger(__name__)


@login_required
def create(request):

    existing_tags = Tag.objects.usage_for_model(
        OwnedWrapper,
        filters=dict(
            user=request.user,
            content_type=OwnedWrapper.t(Presentation)
        )
    )

    selected = request.session.get('selected_records', ())
    next = validate_next_link(
        request.GET.get('next'), reverse('presentation-manage'))

    custom_permissions = getattr(settings, 'PRESENTATION_PERMISSIONS', None)

    class CreatePresentationForm(forms.Form):
        title = forms.CharField(
            label='Title',
            max_length=Presentation._meta.get_field('title').max_length
        )
        add_selected = forms.BooleanField(
            label='Add selected records immediately',
            required=False,
            initial=True
        )
        auth_access = forms.BooleanField(
            label='Set default permissions',
            required=False,
            initial=True
        )

    if request.method == "POST":
        form = CreatePresentationForm(request.POST)
        if form.is_valid():
            hidden = getattr(settings, 'PRESENTATION_HIDE_ON_CREATE', False)
            presentation = Presentation.objects.create(
                title=form.cleaned_data['title'],
                owner=request.user,
                hidden=hidden,
            )
            if form.cleaned_data['add_selected']:
                add_selected_items(request, presentation)

            if form.cleaned_data['auth_access']:
                if not custom_permissions:
                    g = ExtendedGroup.objects.filter(type=AUTHENTICATED_GROUP)
                    g = g[0] if g else ExtendedGroup.objects.create(
                        type=AUTHENTICATED_GROUP, name='Authenticated Users')
                    AccessControl.objects.create(
                        content_object=presentation, usergroup=g, read=True)
                else:
                    for name in custom_permissions:
                        g = ExtendedGroup.objects.filter(name=name)
                        if len(g) == 0:
                            g = Group.objects.filter(name=name)
                        if len(g) == 0:
                            continue
                        AccessControl.objects.create(
                            content_object=presentation,
                            usergroup=g[0],
                            read=True
                        )

            update_actionbar_tags(request, presentation)

            return HttpResponseRedirect(
                reverse(
                    'presentation-edit',
                    kwargs={
                        'id': presentation.id,
                        'name': presentation.name
                    }
                )
            )
    else:
        form = CreatePresentationForm()

    return render(
        request,
        'presentation_create.html',
        {
            'form': form,
            'next': next,
            'selected': selected,
            'existing_tags': existing_tags,
            'can_publish': request.user.has_perm(
                'presentation.publish_presentations'),
            'custom_permissions': custom_permissions,
        }
    )


def add_selected_items(request, presentation):
    selected = request.session.get('selected_records', ())
    records = Record.filter_by_access(request.user, *selected)
    # records may have been returned in different order
    records = dict((r.id, r) for r in records)
    c = presentation.items.count()
    for rid in selected:
        record = records.get(rid)
        if record:
            c += 1
            presentation.items.create(record=record, order=c)
    request.session['selected_records'] = ()


@login_required
def edit(request, id, name):

    presentation = get_object_or_404(filter_by_access(
        request.user, Presentation, write=True, manage=True).filter(id=id))
    existing_tags = [
        t.name
        for t in Tag.objects.usage_for_model(
            OwnedWrapper,
            filters=dict(
                user=request.user,
                content_type=OwnedWrapper.t(Presentation)
            )
        )
    ]
    tags = Tag.objects.get_for_object(
        OwnedWrapper.objects.get_for_object(
            user=request.user, object=presentation
        )
    )

    class PropertiesForm(forms.Form):
        title = forms.CharField(
            label='Title',
            max_length=Presentation._meta.get_field('title').max_length
        )
        hidden = forms.BooleanField(label='Hidden', required=False)
        description = forms.CharField(
            label='Description',
            widget=forms.Textarea(attrs={
                'rows': 5
            }),
            required=False
        )
        password = forms.CharField(
            label='Password',
            required=False,
            max_length=Presentation._meta.get_field('password').max_length
        )
        fieldset = FieldSetChoiceField(
            label='Field set',
            user=presentation.owner
        )
        hide_default_data = forms.BooleanField(
            label='Hide default data',
            required=False
        )

    class BaseOrderingForm(ModelForm):
        record = forms.CharField(widget=forms.HiddenInput)
        annotation = forms.CharField(widget=forms.Textarea, required=False)

        def __init__(self, initial=None, instance=None, *args, **kwargs):
            if instance:
                object_data = dict(annotation=instance.annotation)
            else:
                object_data = dict()
            if initial is not None:
                object_data.update(initial)
            super(BaseOrderingForm, self).__init__(
                initial=object_data, instance=instance, *args, **kwargs)

        def clean_record(self):
            return Record.objects.get(id=self.cleaned_data['record'])

        def save(self, commit=True):
            instance = super(BaseOrderingForm, self).save(commit)
            instance.annotation = self.cleaned_data['annotation']
            return instance

    self_page = HttpResponseRedirect(
        reverse(
            'presentation-edit',
            kwargs={
                'id': presentation.id,
                'name': presentation.name
            }
        )
    )

    ordering_formset = modelformset_factory(
        PresentationItem,
        extra=0,
        can_delete=True,
        exclude=('presentation',),
        form=BaseOrderingForm
    )
    queryset = presentation.items.select_related(
        'record', 'presentation', 'presentation__owner').all()
    if request.method == 'POST' and request.POST.get('update-items'):
        formset = ordering_formset(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            # Explicitly remove deleted objects
            for instance in formset.deleted_objects:
                instance.delete()
            for instance in instances:
                instance.presentation = presentation
                instance.save()
            # trigger modified date update
            presentation.save()
            messages.add_message(
                request,
                messages.INFO,
                message="Changes to presentation items saved successfully."
            )
            return self_page
    else:
        formset = ordering_formset(queryset=queryset)

    if request.method == 'POST' and request.POST.get('add-selected-items'):
        add_selected_items(request, presentation)
        # trigger modified date update
        presentation.save()
        return self_page

    if request.method == "POST" and request.POST.get('update-properties'):

        update_actionbar_tags(request, presentation)

        form = PropertiesForm(request.POST)
        if form.is_valid():
            presentation.title = form.cleaned_data['title']
            presentation.name = None
            if presentation.owner.has_perm(
                    'presentation.publish_presentations'):
                presentation.hidden = form.cleaned_data['hidden']
            presentation.description = form.cleaned_data['description']
            presentation.password = form.cleaned_data['password']
            if form.cleaned_data['fieldset']:
                presentation.fieldset = FieldSet.for_user(
                    presentation.owner).get(id=form.cleaned_data['fieldset'])
            else:
                presentation.fieldset = None
            presentation.hide_default_data = \
                form.cleaned_data['hide_default_data']
            presentation.save()
            messages.add_message(
                request,
                messages.INFO,
                message="Changes to presentation saved successfully."
            )
            return self_page
    else:
        form = PropertiesForm(
            initial={
                'title': presentation.title,
                'hidden': presentation.hidden,
                'description': presentation.description,
                'password': presentation.password,
                'fieldset': presentation.fieldset.id
                if presentation.fieldset else None,
                'hide_default_data': presentation.hide_default_data,
            }
        )

    contenttype = ContentType.objects.get_for_model(Presentation)
    return render(
        request,
        'presentation_properties.html',
        {
            'presentation': presentation,
            'contenttype': "%s.%s" % (
                contenttype.app_label, contenttype.model),
            'formset': formset,
            'form': form,
            'selected_tags': [tag.name for tag in tags],
            'usertags': existing_tags if len(existing_tags) > 0 else None,
        }
    )


@login_required
def manage(request):
    return browse(request, manage=True)


def browse(request, manage=False):

    if manage and not request.user.is_authenticated:
        raise Http404()

    if request.user.is_authenticated and not list(request.GET.items()) and \
            not getattr(settings, 'FORGET_PRESENTATION_BROWSE_FILTER', False):
        # retrieve past settings
        qs = load_settings(
            request.user, filter='presentation_browse_querystring')
        if 'presentation_browse_querystring' in qs:

            # Don't restore the "untagged only" setting, as it confuses
            # a lot of users
            args = qs['presentation_browse_querystring'][0]
            args = '&'.join(
                p for p in args.split('&')
                if not p.startswith('ut=')
            )

            return HttpResponseRedirect(
                '%s?%s' % (
                    reverse('presentation-manage'
                            if manage else 'presentation-browse'),
                    args,
                )
            )

    presenter = request.GET.get('presenter')
    tags = [_f for _f in request.GET.getlist('t') if _f]
    sortby = request.GET.get('sortby')
    if sortby not in ('title', 'created', 'modified'):
        sortby = 'title'
    untagged = 1 if request.GET.get('ut') else 0
    if untagged:
        tags = []
    remove_tag = request.GET.get('rt')
    if remove_tag and remove_tag in tags:
        tags.remove(remove_tag)
    keywords = request.GET.get('kw', '')
    get = request.GET.copy()
    get.setlist('t', tags)
    if 'rt' in get:
        del get['rt']
    if untagged:
        get['ut'] = '1'
    elif 'ut' in get:
        del get['ut']

    if untagged and request.user.is_authenticated:
        qs = TaggedItem.objects.filter(
            content_type=OwnedWrapper.t(OwnedWrapper)
        ).values('object_id').distinct()
        qs = OwnedWrapper.objects.filter(
            user=request.user,
            content_type=OwnedWrapper.t(Presentation),
            id__in=qs
        ).values('object_id')
        q = ~Q(id__in=qs)
    elif tags:
        qs = OwnedWrapper.objects.filter(
            content_type=OwnedWrapper.t(Presentation))
        # get list of matching IDs for each individual tag, since tags
        # may be attached by different owners
        ids = [
            list(
                TaggedItem.objects
                .get_by_model(qs, '"%s"' % tag)
                .values_list('object_id', flat=True)
            ) for tag in tags
        ]
        q = Q(*(Q(id__in=x) for x in ids))
    else:
        q = Q()

    if presenter:
        presenter = User.objects.get(username=presenter)
        qp = Q(owner=presenter)
    else:
        qp = Q()

    if keywords:
        qk = Q(
            *(
                Q(title__icontains=kw)
                | Q(description__icontains=kw)
                | Q(owner__last_name__icontains=kw)
                | Q(owner__first_name__icontains=kw)
                | Q(owner__username__icontains=kw) for kw in keywords.split()
            )
        )
    else:
        qk = Q()

    if manage:
        qv = Q()
        presentations = filter_by_access(
            request.user, Presentation, write=True, manage=True)
    else:
        qv = Presentation.published_q()
        presentations = filter_by_access(request.user, Presentation)

    presentations = presentations.select_related('owner').filter(q, qp, qk, qv)
    presentations = presentations.order_by(
        '-' + sortby if sortby != 'title' else sortby)

    if request.method == "POST":

        if manage and (
            request.POST.get('hide') or request.POST.get('unhide')
        ) and request.user.has_perm('presentation.publish_presentations'):
            hide = request.POST.get('hide') or False
            ids = list(map(int, request.POST.getlist('h')))
            for presentation in Presentation.objects.filter(
                    owner=request.user, id__in=ids):
                presentation.hidden = bool(hide)
                presentation.save()

        if manage and request.POST.get('delete'):
            ids = list(map(int, request.POST.getlist('h')))
            Presentation.objects.filter(
                owner=request.user, id__in=ids).delete()

        get['kw'] = request.POST.get('kw')
        if get['kw'] != request.POST.get('okw') and 'page' in get:
            # user entered keywords, reset page counter
            del get['page']

        if request.POST.get('update_tags'):
            ids = list(map(int, request.POST.getlist('h')))
            update_actionbar_tags(request, *presentations.filter(id__in=ids))

        # check for clicks on "add selected items" buttons
        for button in [k for k in list(request.POST.keys())
                       if k.startswith('add-selected-items-')]:
            id = int(button[len('add-selected-items-'):])
            presentation = get_object_or_404(
                filter_by_access(
                    request.user, Presentation, write=True, manage=True)
                .filter(id=id)
            )
            add_selected_items(request, presentation)
            return HttpResponseRedirect(
                reverse(
                    'presentation-edit',
                    args=(presentation.id, presentation.name)
                )
            )

        return HttpResponseRedirect(request.path + '?' + get.urlencode())

    active_tags = tags

    def col(model, field):
        qn = connection.ops.quote_name
        return '%s.%s' % (
            qn(model._meta.db_table),
            qn(model._meta.get_field(field).column)
        )

    if presentations:
        q = OwnedWrapper.objects.extra(
            tables=(Presentation._meta.db_table,),
            where=(
                '%s=%s' % (
                    col(OwnedWrapper, 'object_id'),
                    col(Presentation, 'id')
                ),
                '%s=%s' % (
                    col(OwnedWrapper, 'user'),
                    col(Presentation, 'owner')
                )
            )
        ).filter(
            object_id__in=presentations.values('id'),
            content_type=OwnedWrapper.t(Presentation)
        )
        tags = Tag.objects.usage_for_queryset(q, counts=True)

        if not manage:
            for p in presentations:
                p.verify_password(request)
    else:
        tags = ()

    if presentations and request.user.is_authenticated:
        usertags = Tag.objects.usage_for_queryset(
            OwnedWrapper.objects.filter(
                user=request.user,
                object_id__in=presentations.values('id'),
                content_type=OwnedWrapper.t(Presentation)
            ),
            counts=True
        )
    else:
        usertags = ()

    presenters = User.objects.filter(presentation__in=presentations) \
        .annotate(presentations=Count('presentation')) \
        .order_by('last_name', 'first_name')

    if request.user.is_authenticated and presentations:
        # save current settings
        querystring = request.GET.urlencode()
        store_settings(
            request.user, 'presentation_browse_querystring', querystring)

    if presentations:
        paginator = Paginator(presentations, 50)
        page = request.GET.get('page')
        try:
            presentations = paginator.page(page)
        except PageNotAnInteger:
            presentations = paginator.page(1)
        except EmptyPage:
            presentations = paginator.page(paginator.num_pages)

    return render(
        request,
        'presentation_browse.html',
        {
            'manage': manage,
            'tags': tags if len(tags) > 0 else None,
            'untagged': untagged,
            'usertags': usertags if len(usertags) > 0 else None,
            'active_tags': active_tags,
            'active_presenter': presenter,
            'presentations': presentations,
            'presenters': presenters if len(presenters) > 1 else None,
            'keywords': keywords,
            'sortby': sortby,
        }
    )


def password(request, id, name):

    presentation = get_object_or_404(
        filter_by_access(request.user, Presentation)
        .filter(Presentation.published_q(request.user), id=id)
    )

    class PasswordForm(forms.Form):
        password = forms.CharField(widget=forms.PasswordInput)

        def clean_password(self):
            p = self.cleaned_data.get('password')
            if p != presentation.password:
                raise forms.ValidationError("Password is not correct.")
            return p

    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            request.session.setdefault(
                'passwords', dict()
            )[presentation.id] = form.cleaned_data.get('password')
            request.session.modified = True
            return HttpResponseRedirect(validate_next_link(
                request.GET.get('next'), reverse('presentation-browse')))
    else:
        form = PasswordForm()

    return render(
        request,
        'presentation_password.html',
        {
            'form': form,
            'presentation': presentation,
            'next': request.GET.get('next', reverse('presentation-browse')),
        }
    )


@require_POST
@login_required
def duplicate(request, id, name):
    presentation = get_object_or_404(
        filter_by_access(request.user, Presentation, write=True, manage=True).
        filter(id=id)
    )
    target_user = None
    username = request.POST.get('user')
    if username:
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.add_message(
                request,
                messages.INFO,
                message="No user with username '%s' exists." %
                        username
            )
            return HttpResponseRedirect(
                reverse('presentation-edit',
                        args=(presentation.id, presentation.name)))

    dup = duplicate_presentation(presentation, target_user or request.user)

    if not target_user:
        return HttpResponseRedirect(
            reverse('presentation-edit', args=(dup.id, dup.name)))
    else:
        messages.add_message(
            request,
            messages.INFO,
            message="A copy of the presentation was created for user '%s'." %
                    username
        )
        return HttpResponseRedirect(
            reverse('presentation-edit',
                    args=(presentation.id, presentation.name)))


@login_required
def record_usage(request, id, name):
    record = Record.get_or_404(id, request.user)
    presentations = Presentation.objects.filter(
        items__record=record).distinct().order_by('title')

    return render(
        request,
        'presentation_record_usage.html',
        {
            'record': record,
            'presentations': presentations,
        }
    )


def get_server(request, offline=False):
    host = request.META.get('HTTP_X_FORWARDED_HOST', request.META['HTTP_HOST'])
    scheme = request.META.get('HTTP_X_FORWARDED_PROTO', 'https')
    port = request.META.get('HTTP_X_FORWARDED_PORT', request.META.get('SERVER_PORT', 443 if scheme == 'https' else 80))
    return '' if offline else scheme + '://' + host + ':' + port


def get_id(request, *args, offline=False):
    s = '/'.join(map(str, args))
    return '%s/%s/' % (get_server(request, offline), s)


def get_metadata(fieldvalues):
    compact = getattr(settings, 'COMPACT_METADATA_VIEW', False)
    markdown_fields = get_fields_for_set('markdown')
    result = []
    for fv in fieldvalues:
        if fv.field_id in markdown_fields:
            value = markdown(fv.value)
        else:
            value = fv.value
        if not compact or not fv.subitem:
            result.append(dict(label=fv.resolved_label, value=value))
        else:
            result[-1]['value'] += '; ' + value
    return result


def slide_manifest(request, slide, owner, offline=False):

    fieldvalues = slide.get_fieldvalues(owner=owner)
    title = title_from_fieldvalues(fieldvalues) or 'Untitled',
    id = get_id(
        request, 'slide', 'canvas', 'slide%d' % slide.id, offline=offline)
    server = get_server(request, offline)
    image = server + slide.record.get_image_url(
        force_reprocess=False,
        handler='storage-retrieve-iiif-image',
    )

    metadata = get_metadata(fieldvalues)
    if slide.annotation:
        metadata.insert(0, dict(label='Annotation', value=slide.annotation))

    passwords = request.session.get('passwords', dict())

    image_path = get_image_for_record(
        slide.record, user=request.user, passwords=passwords)

    width = height = None

    if image_path:
        try:
            width, height = Image.open(image_path).size
            canvas_width = width
            canvas_height = height
        except Exception:
            logger.warning(
                'Could not determine image size for "%s"' % image_path,
                exc_info=True
            )

    if width is None or height is None:
        width = height = None
        canvas_width = 1200
        canvas_height = 1200

    while canvas_height < 1200 or canvas_width < 1200:
        canvas_height *= 2
        canvas_width *= 2

    other_content = []

    if width and height:

        resource = {
            '@id': image,
            '@type': 'dctypes:Image',
            'format': 'image/jpeg',
            "height": height,
            "width": width
        }

        if not offline:
            resource['service'] = {
                '@context': 'http://iiif.io/api/image/2/context.json',
                '@id': image,
                'profile': 'http://iiif.io/api/image/2/level1.json'
            }

            viewers = list(get_viewers_for_object(slide.record, request))
            if len(viewers) > 0:
                other_content.append({
                    '@id': server + reverse(
                        'presentation-annotation-list',
                        kwargs={
                            'id': slide.presentation.id,
                            'name': slide.presentation.name,
                            'slide_id': slide.id,
                        }),
                    '@type': 'sc:AnnotationList',
                })

        images = [{
            '@type': 'oa:Annotation',
            'motivation': 'sc:painting',
            'resource': resource,
            'on': id,
        }]

    else:

        return special_slide(
            request,
            kind='missing',
            label='Missing image',
            index=slide.id,
            offline=offline,
        )

    result = {
        '@id': id,
        '@type': 'sc:Canvas',
        'label': title,
        "height": canvas_height,
        "width": canvas_width,
        'images': images,
        'otherContent': other_content,
        'metadata': metadata,
    }

    contributor_fields = list(standardfield_ids('contributor', equiv=True))
    rights_fields = list(standardfield_ids('rights', equiv=True))

    for fv in fieldvalues:
        if not result.get('license') and fv.refinement == 'license' and fv.field.id in rights_fields:
            result['license'] = fv.value
        elif not result.get('attribution') and not fv.refinement and fv.field.id in contributor_fields:
            result['attribution'] = fv.value

    if offline:
        result['thumbnail'] = {
            '@id': '/thumbs' + image,
        }

    return result


def special_slide(request, kind, label, index=None, offline=False):
    image = get_server(request, offline) + reverse(
        'presentation-%s-slide' % kind,
        kwargs={'extra': str(index) if index else ''}
    )
    id = get_id(
        request, 'slide', 'canvas', 'slide%d' % (index or 0), offline=offline)
    resource = {
        '@id': image,
        '@type': 'dctypes:Image',
        'format': 'image/jpeg',
        "height": 100,
        "width": 100
    }
    if not offline:
        resource['service'] = {
            '@context': 'http://iiif.io/api/image/2/context.json',
            '@id': image,
            'profile': 'http://iiif.io/api/image/2/level1.json'
        }

    result = {
        '@id': id,
        '@type': 'sc:Canvas',
        'label': label,
        "height": 100,
        "width": 100,
        'images': [{
            '@type': 'oa:Annotation',
            'motivation': 'sc:painting',
            'resource': resource,
            'on': id,
        }],
        'metadata': [],
    }

    if offline:
        result['thumbnail'] = {
            '@id': image,
        }

    return result


def raw_manifest(request, id, name, offline=False, end_slide=False):
    p = Presentation.get_by_id_for_request(id, request)
    if not p:
        return dict(result='error')

    owner = request.user if request.user.is_authenticated else None
    slides = p.items.select_related('record').filter(hidden=False)

    extra = [] if not end_slide else [
        special_slide(
            request,
            kind='blank',
            label='End of presentation',
            offline=offline,
        )
    ]

    return {
        '@context': 'http://iiif.io/api/presentation/2/context.json',
        '@type': 'sc:Manifest',
        '@id': get_id(
            request, 'presentation', 'manifest', str(p.id), p.name,
            offline=offline),
        'label': p.title,
        'metadata': [],
        'description': p.description or '',
        'sequences': [{
            '@id': get_id(
                request, 'presentation', 'presentation%d' % p.id, 'all',
                offline=offline),
            '@type': 'sc:Sequence',
            'label': 'All slides',
            'canvases': [
                slide_manifest(
                    request,
                    slide,
                    owner,
                    offline=offline,
                ) for slide in slides
            ] + extra
        }],
    }


def slide_manifest_v3(request, slide, owner, offline=False):

    fieldvalues = slide.get_fieldvalues(owner=owner, hidden=True)
    titles = title_from_fieldvalues(fieldvalues) or ['Untitled'],
    canvas_id = get_id(
        request, 'slide', 'canvas', 'slide%d' % slide.id, offline=offline)
    server = get_server(request, offline)
    image = server + slide.record.get_image_url(
        force_reprocess=False,
        handler='storage-retrieve-iiif-image',
    ).rstrip('/')

    metadata = get_metadata(fv for fv in fieldvalues if not fv.hidden)
    if slide.presentation.owner_id and slide.annotation:
        metadata.insert(0, dict(label='Annotation', value=slide.annotation))

    passwords = request.session.get('passwords', dict())

    image_path = get_image_for_record(
        slide.record, user=request.user, passwords=passwords)

    width = height = None

    if image_path:
        try:
            width, height = Image.open(image_path).size
            canvas_width = width
            canvas_height = height
        except Exception:
            logger.warning(
                'Could not determine image size for "%s"' % image_path,
                exc_info=True
            )

    if width is None or height is None:
        width = height = None
        canvas_width = 1200
        canvas_height = 1200

    while canvas_height < 1200 or canvas_width < 1200:
        canvas_height *= 2
        canvas_width *= 2

    if width and height:

        resource = {
            'id': image + '/0,0,%s,%s/1200,/0/default.jpg' % (width, height),
            'type': 'Image',
            'format': 'image/jpeg',
            "height": height,
            "width": width
        }

        if not offline:
            resource['service'] = {
                '@context': 'http://iiif.io/api/image/2/context.json',
                'id': image,
                'profile': 'http://iiif.io/api/image/2/level1.json'
            }

        images = [{
            'id': get_id(request, 'slide', 'anno', 'slide%d' % slide.id, offline=offline),
            'type': 'Annotation',
            'motivation': 'painting',
            'body': resource,
            'target': canvas_id,
        }]

        gps_regex = re.compile(r'([-+]?\d+[.,]\d+\s*),?(\s*[-+]?\d+[.,]\d+\s*)')
        coordinates = []
        for fv in fieldvalues:
            match = gps_regex.match(fv.value)
            if match:
                coordinates.append((match.group(1), match.group(2)))

        nav_place = {
            'type': 'FeatureCollection',
            'features': [
                {
                    "id": get_id(request, 'geojson', 'slide%d' % slide.id, str(i), offline=offline),
                    "type": "Feature",
                    "properties": {
                        "label": {
                            "none": titles,
                        },
                        "summary": {
                            "none": titles,
                        }
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(coordinate[1]),
                            float(coordinate[0]),
                        ]
                    }
                }
                for i, coordinate in enumerate(coordinates)
            ]
        }

    else:

        return special_slide_v3(
            request,
            kind='missing',
            label='Missing image',
            index=slide.id,
            offline=offline,
        )

    result = {
        'id': canvas_id,
        'type': 'Canvas',
        'label': {"none": titles},
        "height": canvas_height,
        "width": canvas_width,
        'items': [{
            'id': get_id(request, 'slide', 'anno-page', 'slide%d' % slide.id, offline=offline),
            'type': 'AnnotationPage',
            'items': images,
        }],
        'thumbnail': [{
            "id": image + '/full/!200,200/0/default.jpg',
            "type": "Image",
            "format": "image/jpeg",
            "width": 200,
            "height": 200,
            "service": [
                {
                    "id": image,
                    "type": "ImageService2",
                    "profile": "http://iiif.io/api/image/2/level1.json"
                }
            ]
        }],
        'navPlace': nav_place,
        'metadata': [
            {
                'label': {
                    'none': [
                        data['label']
                    ]
                },
                'value': {
                    'none': [
                        data['value']
                    ]
                }
            }
            for data in metadata
        ]
    }

    if offline:
        result['thumbnail'] = {
            'id': '/thumbs' + image,
        }

    return result

def special_slide_v3(request, kind, label, index=None, offline=False):
    image = get_server(request, offline) + reverse(
        'presentation-%s-slide' % kind,
        kwargs={'extra': str(index) if index else ''}
    )
    id = get_id(
        request, 'slide', 'canvas', 'slide%d' % (index or 0), offline=offline)
    resource = {
        'id': image,
        'type': 'dctypes:Image',
        'format': 'image/jpeg',
        "height": 100,
        "width": 100
    }
    if not offline:
        resource['service'] = {
            '@context': 'http://iiif.io/api/image/2/context.json',
            'id': image,
            'profile': 'http://iiif.io/api/image/2/level1.json'
        }

    result = {
        'id': id,
        'type': 'sc:Canvas',
        'label': {"none": [label]},
        "height": 100,
        "width": 100,
        'items': [{
            'type': 'Annotation',
            'motivation': 'sc:painting',
            'resource': resource,
            'on': id,
        }],
        'metadata': [],
    }

    if offline:
        result['thumbnail'] = {
            'id': image,
        }

    return result


def raw_manifest_v3(request, id, name, offline=False, end_slide=False):
    p = Presentation.get_by_id_for_request(id, request)
    if not p:
        return dict(result='error')

    owner = request.user if request.user.is_authenticated else None
    slides = p.items.select_related('record').filter(hidden=False)

    extra = [] if not end_slide else [
        special_slide_v3(
            request,
            kind='blank',
            label='End of presentation',
            offline=offline,
        )
    ]

    return {
        '@context': [
            'http://iiif.io/api/presentation/3/context.json',
            'https://iiif.io/api/extension/navplace/context.json',
        ],
        'type': 'Manifest',
        'id': get_id(
            request, 'presentation', 'manifest-v3', str(p.id), p.name,
            offline=offline),
        'label': {"none": [p.title]},
        'metadata': [],
        'description': {"none": [p.description or '']},
        'items': [
            slide_manifest_v3(
                request,
                slide,
                owner,
                offline=offline,
            ) for slide in slides
        ] + extra,
    }


@json_view
def manifest(request, id, name, offline=False):
    end_slide = bool(request.GET.get('end_slide', False))
    return raw_manifest(request, id, name, offline, end_slide=end_slide)


@json_view
def manifest_v3(request, id, name, offline=False):
    end_slide = bool(request.GET.get('end_slide', False))
    return raw_manifest_v3(request, id, name, offline, end_slide=end_slide)


@json_view
def manifest_from_search_v3(request, id=None, name=None):
    hits, records, _ = search(request, id, name, json=True)

    owner = request.user if request.user.is_authenticated else None

    presentation = Presentation()

    # create temporary slide objects
    slides = [
        PresentationItem(
            id=record.id,
            record=record,
            presentation=presentation,
        ) for record in records or []
    ]

    return {
        '@context': [
            'http://iiif.io/api/presentation/3/context.json',
            'https://iiif.io/api/extension/navplace/context.json',
        ],
        'type': 'Manifest',
        'id': get_server(request) + request.get_full_path(),
        'label': {"none": ['Search Results']},
        'metadata': [],
        'description': {"none": ['%s hits' % hits]},
        'items': [
            slide_manifest_v3(
                request,
                slide,
                owner,
            ) for slide in slides
        ],
    }


@json_view
def annotation_list(request, id, name, slide_id):
    p = Presentation.get_by_id_for_request(id, request)
    if not p:
        return dict(result='error')

    slides = p.items.select_related('record').filter(hidden=False, id=slide_id)

    resources = []

    if slides:
        record = slides[0].record
        viewers = list(get_viewers_for_object(record, request))
        for viewer in viewers:
            if viewer.is_embeddable:
                resources.append({
                    '@type': 'oa:Annotation',
                    'motivation': 'sc:painting',
                    'resource': {
                        '@id': get_server(request) + viewer.url('embed'),
                        '@type': 'dctypes:Text',
                        'format': 'application/mdid',
                    },
                })

    return {
        '@context': 'http://iiif.io/api/presentation/2/context.json',
        '@type': 'sc:Manifest',
        '@id': get_id(
            request, 'presentation', 'presentation%d' % p.id,
            'annotation-list', 'slide%s' % slide_id,
        ),
        'resources': resources,
        'on': get_id(request, 'slide', 'canvas', 'slide%s' % slide_id)
    }


def _get_info_json_for_png(size, url):
    return '{"profile": ["http://iiif.io/api/image/2/level2.json", ' \
           '{"supports": ["canonicalLinkHeader", "profileLinkHeader", ' \
           '"mirroring", "rotationArbitrary", "regionSquare", ' \
           '"sizeAboveFull"], "qualities": ["default"], ' \
           '"formats": ["png"]}], "protocol": "http://iiif.io/api/image", ' \
           '"sizes": [], "height": %d, "width": %d, ' \
           '"@context": "http://iiif.io/api/image/2/context.json", ' \
           '"@id": "%s"}' % (size, size, url)


def transparent_png(request, extra):

    if extra and extra.endswith('info.json'):
        return HttpResponse(
            content=_get_info_json_for_png(
                100,
                get_server(request) + reverse('presentation-blank-slide', kwargs={'extra': ''})
            ),
            content_type='application/json',
        )

    data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42' \
           'mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
    return HttpResponse(
        content=base64.b64decode(data),
        content_type='image/png',
    )


def missing_png(request, extra):

    if extra and extra.endswith('info.json'):
        return HttpResponse(
            content=_get_info_json_for_png(
                200,
                get_server(request) + reverse('presentation-missing-slide', kwargs={'extra': ''})
            ),
            content_type='application/json',
        )

    path = os.path.join(
        os.path.dirname(__file__),
        'static', 'presentation', 'image_unavailable.jpg')
    with open(path, 'rb') as thumbnail:
        return HttpResponse(
            content=thumbnail.read(),
            content_type='image/png',
        )
