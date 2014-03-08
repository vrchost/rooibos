from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
#from forms import PeopleSearchForm
#from models import FlickrUploadr, FlickrSearch, FlickrImportr, FlickrSetPhotos
from os import makedirs
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.settings import FLICKR_KEY, FLICKR_SECRET
from rooibos.solr import SolrIndex
#from rooibos.solr.models import SolrIndexUpdates
from rooibos.storage import Storage, Media
from rooibos.util import json_view
import flickrapi
import urllib, urllib2, time
from . import FlickrSearch
import math
from django.utils.http import urlencode
from rooibos.ui.views import select_record


@login_required
def search(request):

    pagesize = 30  # per Flickr API TOS

    query = request.GET.get('q', '') or request.POST.get('q', '')
    try:
        page = int(request.GET.get('p', 1))
    except ValueError:
        page = 1

    f = FlickrSearch()
    results = f.search(query, page, pagesize) if query else None

    if results['records']:
        # Map URLs to IDs and find out which ones are already selected
        urls = [r['record_url'] for r in results['records']]
        ids = dict(Record.objects.filter(source__in=urls, manager='flickr').values_list('source', 'id'))
        selected = request.session.get('selected_records', ())

        for r in results['records']:
            r['id'] = ids.get(r['record_url'])
            r['selected'] = r['id'] in selected


    pages = int(math.ceil(float(results['hits']) / pagesize)) if results else 0
    prev_page_url = "?" + urlencode((('q', query), ('p', page - 1))) if page > 1 else None
    next_page_url = "?" + urlencode((('q', query), ('p', page + 1))) if page < pages else None


    return render_to_response('flickr-results.html',
                          {'query': query,
                           'results': results,
                           'page': page,
                           'pages': pages,
                           'prev_page': prev_page_url,
                           'next_page': next_page_url,
                          },
                          context_instance=RequestContext(request))




def flickr_select_record(request):

    if not request.user.is_authenticated():
        raise Http404()

    if request.method == "POST":
        f = FlickrSearch()
        remote_ids = simplejson.loads(request.POST.get('id', '[]'))

        # find records that already have been created for the given URLs
        ids = dict(Record.objects.filter(source__in=remote_ids, manager='flickr').values_list('source', 'id'))
        result = []
        for remote_id in remote_ids:
            id = ids.get(remote_id)
            if id:
                result.append(id)
            else:
                record = f.create_record(remote_id)
                result.append(record.id)
        # rewrite request and submit to regular selection code
        r = request.POST.copy()
        r['id'] = simplejson.dumps(result)
        request.POST = r

    return select_record(request)



#
#
#
#flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, cache=True)
#
#def _save_file(targeturl, base, filename):
#    try:
#        req = urllib2.Request(targeturl)
#        response = urllib2.urlopen(req)
#        try:
#            makedirs(base)
#        except Exception:
#            pass
#        image = open('%s/%s' % (base, filename), 'wb')
#        image.write(response.read())
#        image.close()
#    except Exception, detail:
#        print 'Error:', detail
#
#def main(request):
#    return render_to_response('flickr_main.html', {},
#                              context_instance=RequestContext(request))
#
#def authorize(request):
#    return render_to_response('flickr_main.html', {},
#                              context_instance=RequestContext(request))
#
#def people(request, username=None):
#    nsid = None
#    if request.method == 'POST':
#        form = PeopleSearchForm(request.POST)
#        if form.is_valid():
#            username = form.cleaned_data['username']
#            try:
#                e = flickr.people_findByUsername(username=username)
#                nsid = e.find('user').attrib['nsid']
#            except flickrapi.FlickrError:
#                pass
#    else:
#        form = PeopleSearchForm()
#
#    return render_to_response('flickr_people.html', {'form': form, 'nsid':nsid},
#                              context_instance=RequestContext(request))
#
#
#def photosets(request, id=None):
#    try:
#        if id:
#            json = flickr.photosets_getList(user_id=id, format='json')
#            e = flickr.photosets_getList(user_id=id)
#            return render_to_response('flickr_sets.html', {'results': json},
#                                          context_instance=RequestContext(request))
#        else:
#            pass
#    except flickrapi.FlickrError:
#        pass
#
#def flickrSet(request, setid=None):
#    setPhotos = FlickrSetPhotos()
#    id = setid
#    search_page = request.POST.get("search_page", 1)
#    view = request.POST.get("view", "thumb")
#    sort = 'relevance'
#    if request.POST.get("interesting"):
#        sort = 'interestingness-desc'
#    results = setPhotos.setPhotos(id,search_page,sort)
#
#    return render_to_response('flickr_setphotos.html',  {'results':results,'setid':id,'search_page':search_page,'sort':sort,'view':view},
#                                      context_instance=RequestContext(request))
#
#def make_collection(request):
#    storage = Storage.objects.get(name='flickr-full')
#    collection = Collection()
#    pass
#
#def import_set_photos(request):
#    setid = request.POST["setid"]
#    try:
#        if setid:
#            e = flickr.photosets_getInfo(photoset_id=setid)
#            title = e.find("photoset").find("title").text
#            collection, created = Collection.objects.get_or_create(title=title, name=title)
#            if created:
#                collection.save()
#                # ms.append('Created Collection %s' % collection.title)
#
#            extras = 'license, date_upload, date_taken, owner_name, icon_server, original_format, last_update, geo, tags, machine_tags, o_dims, views, media, path_alias, url_sq, url_t, url_s, url_m, url_o'
#            e = flickr.photosets_getPhotos(photoset_id=setid, extras=extras)
#            storage = Storage.objects.get(name='personal-images-full')
#            for photo in e.find('photoset').findall('photo'):
#                record = Record()
#                record.name = photo.attrib['title']
#                record.save(force_insert=True)
#                dc_identifier = Field.objects.get(name='identifier', standard__prefix='dc')
#                dc_title = Field.objects.get(name='title', standard__prefix='dc')
#                record.fieldvalue_set.create(field=dc_identifier, value=photo.attrib['id'])
#                record.fieldvalue_set.create(field=dc_title, value=photo.attrib['title'])
#                record.save()
#                CollectionItem.objects.create(record=record, collection=collection).save()
#                media = Media(record=record,
#                              name='full',
#                              url = photo.attrib['url_m'].split('/')[-1],
#                              storage = storage,
#                              mimetype = 'image/jpeg')
#                              #width = photo.attrib['width_o'],
#                              #height = photo.attrib['height_o'])
#                media.save()
#                _save_file(photo.attrib['url_m'], storage.base, photo.attrib['url_m'].split('/')[-1])
#
#                siu = SolrIndexUpdates(record=record.id)
#                siu.save()
#            si = SolrIndex()
#            si.index()
#            return render_to_response('flickr_setphotos.html', {'results': e},
#                                      context_instance=RequestContext(request))
#        else:
#            pass
#    except flickrapi.FlickrError:
#        pass
#
#
#def export_photo_get_frob(request):
#    filename_array = request.POST.getlist('images[filename]')
#    title_array = request.POST.getlist('images[title]')
#    description_array = request.POST.getlist('images[description]')
#    # tags_array = request.POST.getlist('images[tags]')
#    is_public_array = request.POST.getlist('images[is_public]')
#    is_friend_array = request.POST.getlist('images[is_friend]')
#    is_family_array = request.POST.getlist('images[is_family]')
#
#    images = []
#    length = len(filename_array)
#    for i in range(0, length):
#        images.append( {'filename':filename_array[i],
#                        'imageInfo':{"title": title_array[i],
#                                     'description': description_array[i],
#                                    # 'tags': tags_array[i],
#                                    'is_public': is_public_array[i],
#                                    'is_friend': is_friend_array[i],
#                                    'is_family': is_family_array[i]
#                                }
#                    } )
#
#    request.session["images"] = images
#    uploadr = FlickrUploadr()
#    frob =  uploadr.flickrInstance().auth_getFrob(api_key=FLICKR_KEY)
#    frob = frob[0].text
#
#    auth_url = uploadr.flickrInstance().auth_url('write', frob)
#    return render_to_response('flickr_authenticate_upload.html', { 'auth_url':auth_url },
#                                      context_instance=RequestContext(request))
#
#def export_photo_upload(request):
#    images = request.session.get("images",[])
#    frob = request.GET.get("frob", None)
#
#    # if redirecting from photo search
#    if request.session.get("search_string"):
#        return private_photo_search(request,frob)
#    else:
#        uploadr = FlickrUploadr()
#        try:
#            token = uploadr.flickrInstance().get_token(frob)
#        except Exception, detail:
#            return HttpResponseRedirect('/flickr')
#        errors = []
#        response = 'Success!'
#
#        for image in images:
#            filename = image["filename"]
#            imageInfo = image["imageInfo"]
#            e = uploadr.uploadImage(filename, imageInfo)
#            e= str(e)
#            index = e.find('Error')
#            if index != -1:
#                errors.append(e[e.rfind(':')+1:])
#            index = e.find('Errno')
#            if index != -1:
#                errors.append(e[e.rfind(']')+1:])
#
#        if len(errors) > 0:
#            response = "Errors:<br/><ul>"
#            for error in errors:
#                response += "<li>" + error + "</li>"
#            response += "</ul>"
#        # response= e
#
#        return render_to_response('flickr_main.html', {'response':response},
#                                          context_instance=RequestContext(request))
#
#def export_photo_list(request):
#    selected = request.session.get('selected_records', ())
#
#    result = []
#    records = Record.objects.filter(id__in=selected)
#    for record in records:
#        media = Media.objects.select_related().filter(record=record)
#
#        if request.user == record.owner or record.owner == None: # cmp(record.owner.get_full_name(),request.user.get_full_name()):
#            permission=True
#        else:
#            permission=False
#
#        legend = record.title
#        if legend and len(legend) > 0 and len(legend) > 75:
#            legend = record.title[:75] + "..."
#
#        result.append(dict(id=record.id,
#            legend=legend,
#            title=record.title,
#            record_url=record.get_absolute_url(),
#            img_url=record.get_thumbnail_url(),
#            media_filepath=media[0].get_absolute_file_path(),
#            owner=record.owner,
#            permission=permission
#            )
#        )
#
#
#    return render_to_response('flickr_photo_list.html', {'request':request,'selected':result },
#                                      context_instance=RequestContext(request))
#
#def photo_search(request):
#    if request.GET.get("frob"):
#        private_photo_search(request)
#    if request.POST.get("search_string"):
#        if request.POST.get("private"):
#            request.session["search_string"] = request.POST.get("search_string")
#        else:
#            return public_photo_search(request)
#        return private_search_get_frob(request)
#    else:
#        return render_to_response('flickr_photo_search.html',{'results':{},'search_string':"",'search_page':1,'sort':"",'view':""},
#                context_instance=RequestContext(request))
#
#def private_search_get_frob(request):
#    search_string = request.POST.get("search_string", "")
#    search_page = request.POST.get("search_page", "1")
#    view = request.POST.get("view", "thumb")
#    sort = 'relevance'
#    if request.POST.get("interesting"):
#        sort = 'interestingness-desc'
#    # save parameters to session since request is lost in flickr redirect
#    request.session["search_string"] = search_string
#    request.session["search_page"] = search_page
#    request.session["view"] = view
#    request.session["sort"] = sort
#
#    uploadr = FlickrUploadr()
#    frob =  uploadr.flickrInstance().auth_getFrob(api_key=FLICKR_KEY)
#    frob = frob[0].text
#
#    auth_url = uploadr.flickrInstance().auth_url('write', frob)
#    return render_to_response('flickr_authenticate_upload.html', { 'auth_url':auth_url },
#                                      context_instance=RequestContext(request))
#
#def private_photo_search(request,frob):
#    search_string = request.session.get("search_string")
#    del request.session["search_string"]
#    search_page = request.session.get("search_page")
#    del request.session["search_page"]
#    view = request.session.get("view")
#    del request.session["view"]
#    sort = request.session.get("sort")
#    del request.session["sort"]
#
#    if sort == "interesting":
#        sort = 'interestingness-desc'
#
#    search = FlickrSearch()
#    try:
#        token = search.flickrInstance().get_token(frob)
#    except Exception, detail:
#        return HttpResponseRedirect('/flickr')
#    errors = []
#    page = int(search_page)
#    results = search.photoSearch(search_string, page=1, sort='date-posted-desc', private=1, token=token)
#    return render_to_response('flickr_photo_search.html',  {'results':results,'search_string':search_string,'search_page':search_page,'sort':sort,'view':view,'private':1},
#                              context_instance=RequestContext(request))
#
#def public_photo_search(request):
#    search = FlickrSearch()
#    search_string = request.POST.get("search_string", "")
#    search_page = request.POST.get("search_page", 1)
#    view = request.POST.get("view", "thumb")
#    sort = 'relevance'
#    if request.POST.get("interesting"):
#        sort = 'interestingness-desc'
#    results = search.photoSearch(search_string,search_page,sort)
#
#    return render_to_response('flickr_photo_search.html',  {'results':results,'search_string':search_string,'search_page':search_page,'sort':sort,'view':view},
#                                      context_instance=RequestContext(request))
#
#@json_view
#def select_flickr(request):
#    pass
#    #ids = map(None, request.POST.getlist('id'))
#    #checked = request.POST.get('checked') == 'true'
#    #selected = request.session.get('selected_flickrs', ())
#    #if checked:
#    #    selected = set(selected) | set(ids)
#    #else:
#    #    selected = set(selected) - set(ids)
#    #
#    #result = []
#    #for flickr in selected:
#    #    info = flickr.split('|')
#    #    result.append(dict(id=int(info[0]), title=info[1]))
#    #
#    #request.session['selected_flickrs'] = selected
#    #return dict(status=session_status_rendered(RequestContext(request)), flickrs=result, num_selected=len(result))
#
#def import_photos(request):
#    importr = FlickrImportr()
#    photos = request.session['selected_flickrs']
#
#    imported_photos = []
#    for photo in photos:
#        id = photo.split('|')[0]
#        title = photo.split('|')[1]
#        result = importr.importPhoto(id, title)
#        imported_photos.append(result)
#
#    si = SolrIndex()
#    si.index()
#
#    request.session['selected_flickrs'] = []
#    return render_to_response('flickr_imported_photos.html',  {'photos':imported_photos},
#                                      context_instance=RequestContext(request))
