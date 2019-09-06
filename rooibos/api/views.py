from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.contrib import auth
from django.db.models import Q
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from rooibos.presentation.models import Presentation
from rooibos.solr.views import filter_by_access, search
from rooibos.storage.views import create_proxy_url_if_needed
from rooibos.util import json_view, must_revalidate
from rooibos.util.models import OwnedWrapper
from rooibos.data.models import Collection, Record
from tagging.models import Tag
from rooibos.ui.alternate_password import check_alternate_password

import logging


logger = logging.getLogger(__name__)


@json_view
def collections(request, id=None):
    if id:
        collections = filter_by_access(
            request.user, Collection.objects.filter(id=id))
    else:
        collections = filter_by_access(request.user, Collection)
    return {
        'collections': [
            dict(
                id=c.id,
                name=c.name,
                title=c.title,
                owner=c.owner.username if c.owner else None,
                hidden=c.hidden,
                description=c.description,
                agreement=c.agreement,
                children=list(c.children.all().values_list('id', flat=True)),
            )
            for c in collections
        ]
    }


@csrf_exempt
@json_view
def login(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(username=username, password=password)
        if user is None:
            # normal authentication failed,
            # try alternate password (for MediaViewer)
            logger.debug(
                'Regular authentication failed, trying alternate password')
            user = check_alternate_password(username, password)
        if (user is not None) and user.is_active:
            auth.login(request, user)
            return dict(result='ok',
                        sessionid=request.session.session_key,
                        userid=user.id)
        else:
            return dict(result='Login failed')
    else:
        return dict(result='Invalid method. Use POST.')


@json_view
def logout(request):
    auth.logout(request)
    return dict(result='ok')


def _record_as_json(record, owner=None, context=None,
                    process_url=lambda url: url, dc_mapping_cache=None):
    if dc_mapping_cache is None:
        dc_mapping_cache = dict()

    def get_dc_field(field):
        if field.id not in dc_mapping_cache:
            if field.standard and field.standard.prefix == 'dc':
                dc_mapping_cache[field.id] = field.name
            else:
                equivalents = (
                    field for field in field.get_equivalent_fields()
                    if field.standard and field.standard.prefix == 'dc'
                )
                try:
                    dc_mapping_cache[field.id] = equivalents.next().name
                except StopIteration:
                    pass
        return dc_mapping_cache.get(field.id)

    # don't call record.get_thumbnail_url, since it returns CDN links,
    # which the Desktop MediaViewer cannot handle
    thumbnail_url = reverse(
        'storage-thumbnail', kwargs={'id': record.id, 'name': record.name})

    return dict(
        id=record.id,
        name=record.name,
        title=record.title,
        thumbnail=process_url(thumbnail_url),
        image=process_url(record.get_image_url()),
        metadata=[
            dict(
                label=value.resolved_label,
                value=value.value,
                order=value.order,
                dc=get_dc_field(value.field),
            )
            for value in record.get_fieldvalues(owner=owner, context=context)
        ]
    )


def _records_as_json(records, owner=None, context=None,
                     process_url=lambda url: url):
    dc_mapping_cache = dict()
    return [
        _record_as_json(record, owner, context, process_url, dc_mapping_cache)
        for record in records
    ] if records else []


def _presentation_item_as_json(item, owner=None, process_url=lambda url: url):

    fieldvalues = item.get_fieldvalues(owner=owner)

    data = dict(
        id=item.record.id,
        name=item.record.name,
        title=item.title_from_fieldvalues(fieldvalues) or 'Untitled',
        thumbnail=process_url(item.record.get_thumbnail_url()),
        image=process_url(item.record.get_image_url(
            force_reprocess=getattr(settings, 'FORCE_SLIDE_REPROCESS', False)
        )),
        metadata=[
            dict(
                label=value.resolved_label,
                value=value.value
            )
            for value in fieldvalues
        ]
    )
    annotation = item.annotation
    if annotation:
        data['metadata'].append(dict(label='Annotation', value=annotation))
    return data


def _presentation_items_as_json(
        items, owner=None, process_url=lambda url: url):
    return [
        _presentation_item_as_json(item, owner, process_url)
        for item in items
    ]


@json_view
def api_search(request, id=None, name=None):
    hits, records, viewmode = search(request, id, name, json=True)
    return dict(hits=hits,
                records=_records_as_json(records, owner=request.user))


@json_view
def record(request, id, name):
    record = Record.get_or_404(id, request.user)
    return dict(record=_record_as_json(record, owner=request.user))


@json_view
def presentations_for_current_user(request):

    def tags_for_presentation(presentation):
        ownedwrapper = OwnedWrapper.objects.get_for_object(
            request.user, presentation)
        return [
            tag.name
            for tag in Tag.objects.get_for_object(ownedwrapper)
        ]

    if request.user.is_anonymous():
        return dict(presentations=[])
    presentations = Presentation.objects \
        .filter(owner=request.user).order_by('title')
    return {
        'presentations': [
            dict(id=p.id,
                 name=p.name,
                 title=p.title,
                 hidden=p.hidden,
                 description=p.description,
                 created=p.created.isoformat(),
                 modified=p.modified.isoformat(),
                 tags=tags_for_presentation(p))
            for p in presentations
        ]
    }


@must_revalidate
@json_view
def presentation_detail(request, id):
    p = Presentation.get_by_id_for_request(id, request)
    if not p:
        return dict(result='error')

    flash = request.GET.get('flash') == '1'

    # Propagate the flash URL paramater into all image URLs to control the
    # "Vary: cookie" header that breaks caching in Flash/Firefox.  Also add
    # the username from the request to make sure
    # different users don't use each other's cached images.
    def add_flash_parameter(url, request):
        u = create_proxy_url_if_needed(url, request)
        if flash:
            userid = request.user.id if request.user.is_authenticated() else -1
            joiner = '&' if u.find('?') > -1 else '?'
            u = u + joiner + ('flash=1&user=%s' % userid)
        return u

    content = _presentation_items_as_json(
        p.items.select_related('record').filter(hidden=False),
        owner=request.user if request.user.is_authenticated() else None,
        process_url=lambda url: add_flash_parameter(url, request)
    )

    return dict(
        id=p.id,
        name=p.name,
        title=p.title,
        hidden=p.hidden,
        description=p.description,
        created=p.created.isoformat(),
        modified=p.modified.isoformat(),
        content=content,
    )


@must_revalidate
@json_view
def keep_alive(request):
    return dict(user=request.user.username if request.user else '')


@cache_control(no_cache=True)
def autocomplete_user(request):
    query = request.GET.get('q', '').lower()
    try:
        limit = max(10, min(25, int(request.GET.get('limit', '10'))))
    except ValueError:
        limit = 10
    if not query or not request.user.is_authenticated():
        return HttpResponse(content='')
    users = list(User.objects
                 .filter(username__istartswith=query)
                 .order_by('username')
                 .values_list('username', flat=True)[:limit])
    if len(users) < limit:
        users.extend(
            User.objects
                .filter(~Q(username__istartswith=query),
                        username__icontains=query)
                .order_by('username')
                .values_list('username', flat=True)[:limit - len(users)])
    return HttpResponse(content='\n'.join(users))


@cache_control(no_cache=True)
def autocomplete_group(request):
    query = request.GET.get('q', '').lower()
    try:
        limit = max(10, min(25, int(request.GET.get('limit', '10'))))
    except ValueError:
        limit = 10
    if not query or not request.user.is_authenticated():
        return HttpResponse(content='')
    groups = list(Group.objects
                  .filter(name__istartswith=query)
                  .order_by('name')
                  .values_list('name', flat=True)[:limit])
    if len(groups) < limit:
        groups.extend(
            Group.objects
            .filter(~Q(name__istartswith=query), name__icontains=query)
            .order_by('name')
            .values_list('name', flat=True)[:limit - len(groups)]
        )
    return HttpResponse(content='\n'.join(groups))
