from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory, BaseModelFormSet, ModelForm
from django.db.models.aggregates import Count
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import backend
from django.contrib.auth.models import Permission
from django import forms
from django.views.decorators.http import require_POST
from rooibos.contrib.tagging.models import Tag, TaggedItem
from rooibos.contrib.tagging.forms import TagField
from rooibos.contrib.tagging.utils import parse_tag_input
from rooibos.util.models import OwnedWrapper
from rooibos.access import filter_by_access
from rooibos.util import json_view
from rooibos.storage.models import ProxyUrl
from rooibos.data.models import FieldSet, Record
from rooibos.data.forms import FieldSetChoiceField
from rooibos.ui.actionbar import update_actionbar_tags
from rooibos.access.models import ExtendedGroup, AUTHENTICATED_GROUP, AccessControl
from rooibos.userprofile.views import load_settings, store_settings
from models import Presentation, PresentationItem
from functions import duplicate_presentation
import logging
import base64


@login_required
def create(request):

    existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))

    selected = request.session.get('selected_records', ())
    next = request.GET.get('next', '') or reverse('presentation-manage')

    class CreatePresentationForm(forms.Form):
        title = forms.CharField(label='Title', max_length=Presentation._meta.get_field('title').max_length)
        add_selected = forms.BooleanField(label='Add selected records immediately', required=False, initial=True)
        auth_access = forms.BooleanField(label='Allow access to authenticated users', required=False, initial=True)

    if request.method == "POST":
        form = CreatePresentationForm(request.POST)
        if form.is_valid():
            presentation = Presentation.objects.create(title=form.cleaned_data['title'],
                                                       owner=request.user)
            if form.cleaned_data['add_selected']:
                add_selected_items(request, presentation)

            if form.cleaned_data['auth_access']:
                g = ExtendedGroup.objects.filter(type=AUTHENTICATED_GROUP)
                g = g[0] if g else ExtendedGroup.objects.create(type=AUTHENTICATED_GROUP, name='Authenticated Users')
                AccessControl.objects.create(content_object=presentation, usergroup=g, read=True)

            update_actionbar_tags(request, presentation)

            return HttpResponseRedirect(reverse('presentation-edit', kwargs={'id': presentation.id, 'name': presentation.name}))
    else:
        form = CreatePresentationForm()

    return render_to_response('presentation_create.html',
                          {'form': form,
                           'next': next,
                           'selected': selected,
                           'existing_tags': existing_tags,
                           },
                          context_instance=RequestContext(request))


def add_selected_items(request, presentation):
    selected = request.session.get('selected_records', ())
    records = Record.filter_by_access(request.user, *selected)
    c = presentation.items.count()
    for record in records:
        c += 1
        presentation.items.create(record=record, order=c)
    request.session['selected_records'] = ()


@login_required
def edit(request, id, name):

    presentation = get_object_or_404(filter_by_access(
        request.user, Presentation, write=True, manage=True).filter(id=id))
    existing_tags = [t.name for t in Tag.objects.usage_for_model(
        OwnedWrapper, filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))]
    tags = Tag.objects.get_for_object(
        OwnedWrapper.objects.get_for_object(user=request.user, object=presentation))

    class PropertiesForm(forms.Form):
        title = forms.CharField(label='Title', max_length=Presentation._meta.get_field('title').max_length)
#        tags = SplitTaggingField(label='Tags', choices=[(t, t) for t in existing_tags],
#                                         required=False, add_label='Additional tags')
        hidden = forms.BooleanField(label='Hidden', required=False)
        description = forms.CharField(label='Description',
                                      widget=forms.Textarea(attrs={'rows': 5}), required=False)
        password = forms.CharField(label='Password', required=False,
                                   max_length=Presentation._meta.get_field('password').max_length)
        fieldset = FieldSetChoiceField(label='Field set', user=presentation.owner)
        hide_default_data = forms.BooleanField(label='Hide default data', required=False)


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
            super(BaseOrderingForm, self).__init__(initial=object_data, instance=instance, *args, **kwargs)

        def clean_record(self):
            return Record.objects.get(id=self.cleaned_data['record'])

        def save(self, commit=True):
            instance = super(BaseOrderingForm, self).save(commit)
            instance.annotation = self.cleaned_data['annotation']
            return instance

    self_page = HttpResponseRedirect(
        reverse('presentation-edit', kwargs={'id': presentation.id, 'name': presentation.name}))

    OrderingFormSet = modelformset_factory(PresentationItem, extra=0, can_delete=True,
                                           exclude=('presentation'), form=BaseOrderingForm)
    queryset = presentation.items.select_related('record', 'presentation', 'presentation__owner').all()
    if request.method == 'POST' and request.POST.get('update-items'):
        formset = OrderingFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.presentation = presentation
                instance.save()
            request.user.message_set.create(message="Changes to presentation items saved successfully.")
            return self_page
    else:
        formset = OrderingFormSet(queryset=queryset)

    if request.method == 'POST' and request.POST.get('add-selected-items'):
        add_selected_items(request, presentation)
        return self_page

    if request.method == "POST" and request.POST.get('update-properties'):

        update_actionbar_tags(request, presentation)

        form = PropertiesForm(request.POST)
        if form.is_valid():
            presentation.title = form.cleaned_data['title']
            presentation.name = None
            if presentation.owner.has_perm('presentation.publish_presentations'):
                presentation.hidden = form.cleaned_data['hidden']
            presentation.description = form.cleaned_data['description']
            presentation.password = form.cleaned_data['password']
            presentation.fieldset = FieldSet.for_user(presentation.owner).get(id=form.cleaned_data['fieldset']) if form.cleaned_data['fieldset'] else None
            presentation.hide_default_data = form.cleaned_data['hide_default_data']
            presentation.save()
            request.user.message_set.create(message="Changes to presentation saved successfully.")
            return self_page
    else:
        form = PropertiesForm(initial={'title': presentation.title,
                               'hidden': presentation.hidden,
                               'description': presentation.description,
                               'password': presentation.password,
                               'hidden': presentation.hidden,
                               'fieldset': presentation.fieldset.id if presentation.fieldset else None,
                               'hide_default_data': presentation.hide_default_data,
                               })

    contenttype = ContentType.objects.get_for_model(Presentation)
    return render_to_response('presentation_properties.html',
                      {'presentation': presentation,
                       'contenttype': "%s.%s" % (contenttype.app_label, contenttype.model),
                       'formset': formset,
                       'form': form,
                       'selected_tags': [tag.name for tag in tags],
                       'usertags': existing_tags if len(existing_tags) > 0 else None,
                       },
                      context_instance=RequestContext(request))


@login_required
def manage(request):
    return browse(request, manage=True)


def browse(request, manage=False):

    if manage and not request.user.is_authenticated():
        raise Http404()

    if request.user.is_authenticated() and not request.GET.items():
        # retrieve past settings
        qs = load_settings(request.user, filter='presentation_browse_querystring')
        if qs.has_key('presentation_browse_querystring'):
            return HttpResponseRedirect('%s?%s' % (
                reverse('presentation-manage' if manage else 'presentation-browse'),
                qs['presentation_browse_querystring'][0],
                ))

    presenter = request.GET.get('presenter')
    tags = filter(None, request.GET.getlist('t'))
    untagged = 1 if request.GET.get('ut') else 0
    if untagged:
        tags = []
    remove_tag = request.GET.get('rt')
    if remove_tag and remove_tag in tags:
        tags.remove(remove_tag)
    keywords = request.GET.get('kw', '')
    get = request.GET.copy()
    get.setlist('t', tags)
    if get.has_key('rt'):
        del get['rt']
    if untagged:
        get['ut'] = '1'
    elif get.has_key('ut'):
        del get['ut']

    if request.user.is_authenticated():
        existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))
    else:
        existing_tags = ()


    if untagged and request.user.is_authenticated():
        qs = TaggedItem.objects.filter(content_type=OwnedWrapper.t(OwnedWrapper)).values('object_id').distinct()
        qs = OwnedWrapper.objects.filter(user=request.user, content_type=OwnedWrapper.t(Presentation), id__in=qs).values('object_id')
        q = ~Q(id__in=qs)
    elif tags:
        qs = OwnedWrapper.objects.filter(content_type=OwnedWrapper.t(Presentation))
        # get list of matching IDs for each individual tag, since tags may be attached by different owners
        ids = [list(TaggedItem.objects.get_by_model(qs, '"%s"' % tag).values_list('object_id', flat=True)) for tag in tags]
        q = Q(*(Q(id__in=x) for x in ids))
    else:
        q = Q()

    if presenter:
        presenter = User.objects.get(username=presenter)
        qp = Q(owner=presenter)
    else:
        qp = Q()

    if keywords:
        qk = Q(*(Q(title__icontains=kw) | Q(description__icontains=kw) |
                 Q(owner__last_name__icontains=kw) | Q(owner__first_name__icontains=kw) |
                 Q(owner__username__icontains=kw) for kw in keywords.split()))
    else:
        qk = Q()

    if manage:
        qv = Q()
        presentations = filter_by_access(request.user, Presentation, write=True, manage=True)
    else:
        qv = Presentation.published_Q()
        presentations = filter_by_access(request.user, Presentation)

    presentations = presentations.select_related('owner').filter(q, qp, qk, qv).order_by('title')

    if request.method == "POST":

        if manage and (request.POST.get('hide') or request.POST.get('unhide')) and request.user.has_perm('presentation.publish_presentations'):
            hide = request.POST.get('hide') or False
            ids = map(int, request.POST.getlist('h'))
            for presentation in Presentation.objects.filter(owner=request.user, id__in=ids):
                presentation.hidden = hide
                presentation.save()

        if manage and request.POST.get('delete'):
            ids = map(int, request.POST.getlist('h'))
            Presentation.objects.filter(owner=request.user, id__in=ids).delete()

        get['kw'] = request.POST.get('kw')
        if get['kw'] != request.POST.get('okw') and get.has_key('page'):
            # user entered keywords, reset page counter
            del get['page']

        if request.POST.get('update_tags'):
            ids = map(int, request.POST.getlist('h'))
            update_actionbar_tags(request, *presentations.filter(id__in=ids))

        # check for clicks on "add selected items" buttons
        for button in filter(lambda k: k.startswith('add-selected-items-'), request.POST.keys()):
            id = int(button[len('add-selected-items-'):])
            presentation = get_object_or_404(
                filter_by_access(request.user, Presentation, write=True, manage=True).filter(id=id))
            add_selected_items(request, presentation)
            return HttpResponseRedirect(reverse('presentation-edit', args=(presentation.id, presentation.name)))

        return HttpResponseRedirect(request.path + '?' + get.urlencode())


    active_tags = tags
    active_presenter = presenter

    def col(model, field):
        qn = backend.DatabaseOperations().quote_name
        return '%s.%s' % (qn(model._meta.db_table), qn(model._meta.get_field(field).column))

    if presentations and not manage:
        q = OwnedWrapper.objects.extra(
            tables=(Presentation._meta.db_table,),
            where=('%s=%s' % (col(OwnedWrapper, 'object_id'), col(Presentation, 'id')),
                   '%s=%s' % (col(OwnedWrapper, 'user'), col(Presentation, 'owner')))).filter(
            object_id__in=presentations.values('id'),
            content_type=OwnedWrapper.t(Presentation))
        tags = Tag.objects.usage_for_queryset(q, counts=True)

        for p in presentations:
            p.verify_password(request)
    else:
        tags = ()

    if presentations and request.user.is_authenticated():
        usertags = Tag.objects.usage_for_queryset(OwnedWrapper.objects.filter(
                        user=request.user,
                        object_id__in=presentations.values('id'),
                        content_type=OwnedWrapper.t(Presentation)), counts=True)
    else:
        usertags = ()

    presenters = User.objects.filter(presentation__in=presentations) \
                     .annotate(presentations=Count('presentation')).order_by('last_name', 'first_name')

    if request.user.is_authenticated() and presentations:
        # save current settings
        querystring = request.GET.urlencode()
        store_settings(request.user, 'presentation_browse_querystring', querystring)

    return render_to_response('presentation_browse.html',
                          {'manage': manage,
                           'tags': tags if len(tags) > 0 else None,
                           'untagged': untagged,
                           'usertags': usertags if len(usertags) > 0 else None,
                           'active_tags': active_tags,
                           'active_presenter': presenter,
                           'presentations': presentations,
                           'presenters': presenters if len(presenters) > 1 else None,
                           'keywords': keywords,
                           },
                          context_instance=RequestContext(request))

def password(request, id, name):

    presentation = get_object_or_404(
        filter_by_access(request.user, Presentation).filter(
        Presentation.published_Q(request.user), id=id))

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
            request.session.setdefault('passwords', dict())[presentation.id] = form.cleaned_data.get('password')
            request.session.modified = True
            return HttpResponseRedirect(request.GET.get('next', reverse('presentation-browse')))
    else:
        form = PasswordForm()

    return render_to_response('presentation_password.html',
                          {'form': form,
                           'presentation': presentation,
                           'next': request.GET.get('next', reverse('presentation-browse')),
                           },
                          context_instance=RequestContext(request))


@require_POST
@login_required
def duplicate(request, id, name):
    presentation = get_object_or_404(
        filter_by_access(request.user, Presentation, write=True, manage=True).
        filter(id=id))
    dup = duplicate_presentation(presentation, request.user)
    return HttpResponseRedirect(reverse('presentation-edit',
                                        args=(dup.id, dup.name)))


@login_required
def record_usage(request, id, name):
    record = Record.get_or_404(id, request.user)
    presentations = Presentation.objects.filter(items__record=record).distinct().order_by('title')

    return render_to_response('presentation_record_usage.html',
                       {'record': record,
                        'presentations': presentations,
                        },
                       context_instance=RequestContext(request))
