from django.http import HttpResponse, HttpResponseRedirect
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
from rooibos.contrib.tagging.models import Tag, TaggedItem
from rooibos.contrib.tagging.forms import TagField
from rooibos.contrib.tagging.utils import parse_tag_input
from rooibos.util.models import OwnedWrapper
from rooibos.access import filter_by_access, accessible_ids
from rooibos.ui.forms import SplitTaggingField
from rooibos.util import json_view
from rooibos.storage.models import ProxyUrl
from rooibos.data.models import FieldSet, Record
from rooibos.data.forms import FieldSetChoiceField
from models import Presentation, PresentationItem
import logging


@login_required
def create(request):

    existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))

    selected = request.session.get('selected_records', ())
    next = request.GET.get('next', '') or reverse('presentation-manage')

    class CreatePresentationForm(forms.Form):
        title = forms.CharField(label='Title', max_length=Presentation._meta.get_field('title').max_length)
        tags = SplitTaggingField(label='Tags', choices=[(t, t) for t in existing_tags],
                    required=False, add_label='Additional tags')
        add_selected = forms.BooleanField(label='Add selected records immediately', required=False, initial=True)

    if request.method == "POST":
        form = CreatePresentationForm(request.POST)
        if form.is_valid():
            presentation = Presentation.objects.create(title=form.cleaned_data['title'],
                                                       owner=request.user)
            if form.cleaned_data['add_selected']:
                for order,record in enumerate(selected):
                    PresentationItem.objects.create(presentation=presentation, record_id=record, order=order)
                request.session['selected_records'] = ()
            Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                    form.cleaned_data['tags'])
            return HttpResponseRedirect(next)
    else:
        form = CreatePresentationForm()

    return render_to_response('presentation_create.html',
                          {'form': form,
                           'next': next,
                           'selected': selected,
                           },
                          context_instance=RequestContext(request))


@login_required
def edit(request, id, name):

    presentation = get_object_or_404(Presentation.objects.filter(
        id=id, id__in=accessible_ids(request.user, Presentation, write=True, manage=True)))
    existing_tags = [t.name for t in Tag.objects.usage_for_model(
        OwnedWrapper, filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))]
    tags = Tag.objects.get_for_object(
        OwnedWrapper.objects.get_for_object(user=request.user, object=presentation))
    
    class PropertiesForm(forms.Form):
        title = forms.CharField(label='Title', max_length=Presentation._meta.get_field('title').max_length)
        tags = SplitTaggingField(label='Tags', choices=[(t, t) for t in existing_tags],
                                         required=False, add_label='Additional tags')
        hidden = forms.BooleanField(label='Hidden', required=False)
        description = forms.CharField(label='Description', widget=forms.Textarea, required=False)
        password = forms.CharField(label='Password', required=False,
                                   max_length=Presentation._meta.get_field('password').max_length)
        fieldset = FieldSetChoiceField(label='Field set', user=request.user)
        hide_default_data = forms.BooleanField(label='Hide default data', required=False)
        

    if request.method == "POST":
        form = PropertiesForm(request.POST)
        if form.is_valid():
            presentation.title = form.cleaned_data['title']
            presentation.name = None
            if request.user.has_perm('presentation.publish_presentations'):
                presentation.hidden = form.cleaned_data['hidden']
            presentation.description = form.cleaned_data['description']
            presentation.password = form.cleaned_data['password']
            presentation.fieldset = form.cleaned_data['fieldset']
            presentation.hide_default_data = form.cleaned_data['hide_default_data']
            presentation.save()
            Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                    form.cleaned_data['tags'])
            request.user.message_set.create(message="Changes to presentation saved successfully.")
            return HttpResponseRedirect(reverse('presentation-edit', kwargs={'id': presentation.id, 'name': presentation.name}))
    else:
        form = PropertiesForm(initial={'title': presentation.title,
                               'hidden': presentation.hidden,
                               'tags': tags,
                               'description': presentation.description,
                               'hidden': presentation.hidden,
                               'fieldset': presentation.fieldset.id if presentation.fieldset else None,
                               'hide_default_data': presentation.hide_default_data,
                               })

    return render_to_response('presentation_properties.html',
                      {'presentation': presentation,
                       'form': form,},
                      context_instance=RequestContext(request))


@login_required
def items(request, id, name):

    presentation = get_object_or_404(Presentation.objects.filter(
        id=id, id__in=accessible_ids(request.user, Presentation, write=True, manage=True)))

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
        
    OrderingFormSet = modelformset_factory(PresentationItem, extra=0, can_delete=True,
                                           exclude=('presentation'), form=BaseOrderingForm)
    queryset = presentation.items.select_related('record').all()
    if request.method == 'POST':
        formset = OrderingFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.presentation = presentation
                instance.save()
            request.user.message_set.create(message="Changes to presentation items saved successfully.")
            return HttpResponseRedirect(reverse('presentation-items', kwargs={'id': presentation.id, 'name': presentation.name}))
    else:
        formset = OrderingFormSet(queryset=queryset)

    contenttype = ContentType.objects.get_for_model(Presentation)

    return render_to_response('presentation_items.html',
                      {'presentation': presentation,
                       'contenttype': "%s.%s" % (contenttype.app_label, contenttype.model),
                       'formset': formset,},
                      context_instance=RequestContext(request))


@login_required
def manage(request):
    return browse(request, manage=True)
    

def browse(request, manage=False):

    if manage and not request.user.is_authenticated():
        raise Http404()

    presenter = request.user if manage else request.GET.get('presenter')
    tags = filter(None, request.GET.getlist('t'))
    remove_tag = request.GET.get('rt')
    if remove_tag and remove_tag in tags:
        tags.remove(remove_tag)
    keywords = request.GET.get('kw', '')
    get = request.GET.copy()
    get.setlist('t', tags)
    if get.has_key('rt'):
        del get['rt']    

    if request.user.is_authenticated():
        existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))
    else:
        existing_tags = ()

    if tags:
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
    else:
        qv = Presentation.published_Q()
            
    presentations = Presentation.objects.select_related('owner').filter(q, qp, qk, qv,
                                                                        id__in=accessible_ids(request.user, Presentation)).order_by('title')

    class ManagePresentationsForm(forms.Form):
       tags = SplitTaggingField(label='Select existing tags:',
                                choices=[(t, t) for t in existing_tags],
                                required=False,
                                add_label='Enter additional tags:')
       mode = forms.ChoiceField(label='Action',
                                required=True,
                                choices=[('add', 'Add to existing tags'),
                                         ('replace', 'Replace existing tags'),
                                         ('remove', 'Remove existing tags')],
                                initial='add')

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
        
        if request.POST.get('keywords_go'):
            get['kw'] = request.POST.get('kw')
            return HttpResponseRedirect(request.path + '?' + get.urlencode())
            
        if request.POST.get('update_tags'):
            ids = map(int, request.POST.getlist('h'))
            form = ManagePresentationsForm(request.POST)
            if form.is_valid():
                action = form.cleaned_data['mode']
                for presentation in presentations.filter(id__in=ids):
                    if action == 'replace':
                        Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                                form.cleaned_data['tags'])
                    elif action == 'add':
                        for tag in parse_tag_input(form.cleaned_data['tags']):
                            Tag.objects.add_tag(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                                '"%s"' % tag)
                    elif action == 'remove':
                        Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation), '')
                        
        return HttpResponseRedirect(request.get_full_path())
    else:
        form = ManagePresentationsForm()


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

    return render_to_response('presentation_browse.html',
                          {'manage': manage,
                           'tags': tags if len(tags) > 0 else None,
                           'usertags': usertags if len(usertags) > 0 else None,
                           'active_tags': active_tags,
                           'active_presenter': presenter,
                           'presentations': presentations,
                           'presenters': presenters if len(presenters) > 1 else None,
                           'keywords': keywords,
                           'form': form,
                           },
                          context_instance=RequestContext(request))

def password(request, id, name):
    
    presentation = get_object_or_404(Presentation.objects.filter(Presentation.published_Q(request.user),
                                id=id,
                                id__in=accessible_ids(request.user, Presentation)))
    
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
            return HttpResponseRedirect(request.GET.get('next', reverse('presentation-browse')))
    else:
        form = PasswordForm()
        
    return render_to_response('presentation_password.html',
                          {'form': form,
                           'presentation': presentation,
                           'next': request.GET.get('next', reverse('presentation-browse')),
                           },
                          context_instance=RequestContext(request))