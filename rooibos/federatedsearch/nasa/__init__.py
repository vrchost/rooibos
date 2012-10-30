from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import simplejson
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from rooibos.federatedsearch.models import FederatedSearch, HitCount
from rooibos.storage.models import *
from BeautifulSoup import BeautifulSoup
from rooibos.workers.models import JobInfo
from urllib import urlencode
import datetime
import mimetypes
import re
import urllib2

class NasaImageExchange(FederatedSearch):

    SERVER = "http://nix.nasa.gov/"

    def _get_form_defaults(self, form):
        data = {}
        for i in form.findAll('input', attrs={'name': True, 'type': lambda t: t != 'reset'}):
            data[i['name']] = i.get('value') or ''
        for i in form.findAll('select', attrs={'name': True}):
            data[i['name']] = i.find('option', selected=True).get('value') or ''
        return data

    _fix_record_url_re = re.compile(r';jsessionid=\w+')

    def _parse_result_page(self, soup):
        tags = [tag.parent.parent.parent for tag in soup.findAll(text='+ More Details')]
        return [
            {'thumb_url': tag.a.img['src'],
             'title': tag.span.contents[2].strip(),
             'record_url': self._fix_record_url_re.sub('', tag.find(text='+ More Details').parent['href'])}
            for tag in tags
        ]

    def hits_count(self, keyword):
        soup = BeautifulSoup(urllib2.urlopen(self.SERVER))
        data = self._get_form_defaults(soup.form)
        data['qa'] = keyword
        soup = BeautifulSoup(urllib2.urlopen(soup.form['action'], urlencode(data)))
        if soup.find(text="No matches found."):
            return 0
        try:
            return int(soup.findAll('span')[-1].contents[0])
        except:
            pass
        result = self._parse_result_page(soup)
        return len(result)

    def get_label(self):
        return "NASA Image eXchange"

    def get_source_id(self):
        return "NIX"

    def get_search_url(self):
        return reverse('nasa-nix-search')

    def get_collection(self):
        collection, created = Collection.objects.get_or_create(name='nix',
                                                               defaults=dict(
                                                                title='NASA Image eXchange',
                                                                hidden=True,
                                                                description='NASA Multimedia Collection'
                                                               ))
        if created:
            authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
            AccessControl.objects.create(content_object=collection,
                                         usergroup=authenticated_users,
                                         read=True)
        return collection


    def get_storage(self):
        storage, created = Storage.objects.get_or_create(name='nix',
                                                         defaults=dict(
                                                            title='NASA Image eXchange',
                                                            system='local',
                                                            base=os.path.join(settings.AUTO_STORAGE_DIR, 'nix')
                                                         ))
        if created:
            authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
            AccessControl.objects.create(content_object=storage,
                                         usergroup=authenticated_users,
                                         read=True)
        return storage

    def search(self, keyword):
        if not keyword:
            return None
        cached, created = HitCount.current_objects.get_or_create(
            source=self.get_source_id(), query=keyword,
            defaults=dict(hits=0, valid_until=datetime.datetime.now() + datetime.timedelta(1)))
        if not created and cached.results:
            return simplejson.loads(cached.results)

        soup = BeautifulSoup(urllib2.urlopen(self.SERVER))
        data = self._get_form_defaults(soup.form)
        data['qa'] = keyword
        soup = BeautifulSoup(urllib2.urlopen(soup.form['action'], urlencode(data)))
        if soup.find(text="No matches found."):
            return None
        result = self._parse_result_page(soup)
        # get additional result pages
        additional = soup.find(text='red')
        if additional:
            for page in [tag['href'] for tag in additional.parent.parent.findAll('a')]:
                result += self._parse_result_page(BeautifulSoup(urllib2.urlopen(page)))

        cached.results = simplejson.dumps(result, separators=(',', ':'))
        cached.save()
        return result

    def create_record(self, url):
        collection = self.get_collection()

        s = BeautifulSoup(urllib2.urlopen(url))

        def sort_by_dimension(entry):
            m = re.search(r'(?P<width>\d+) x (?P<height>\d+)', entry[1])
            return int(m.group('width')) * int(m.group('height')) if m else 0

        # get metadata
        date = s.find(text='Date:&nbsp;').parent.findNextSibling('td').next
        title = s.find(text='Title:&nbsp;').parent.findNextSibling('td').next
        description = s.find(text='Description:&nbsp;').parent.findNextSibling('td').next
        id = s.find(text='ID:&nbsp;').parent.findNextSibling('td').next
        credit_url = s.find(text='Credit:&nbsp;').parent.findNextSibling('td').findNext('a')['href']
        credit_title = s.find(text='Credit:&nbsp;').parent.findNextSibling('td').findNext('a').next

        record = Record.objects.create(name=title,
                                       source=url,
                                       manager='nasaimageexchange')

        FieldValue.objects.create(record=record,
                                  field=standardfield('title'),
                                  order=0,
                                  value=title)
        FieldValue.objects.create(record=record,
                                  field=standardfield('description'),
                                  order=1,
                                  value=description)
        FieldValue.objects.create(record=record,
                                  field=standardfield('date'),
                                  order=2,
                                  value=date)
        FieldValue.objects.create(record=record,
                                  field=standardfield('identifier'),
                                  order=3,
                                  value=id)
        FieldValue.objects.create(record=record,
                                  field=standardfield('contributor'),
                                  order=4,
                                  value=credit_title)
        FieldValue.objects.create(record=record,
                                  field=standardfield('contributor'),
                                  order=5,
                                  value=credit_url)

        CollectionItem.objects.create(collection=collection, record=record)

        # media links and dimensions
        media = [(a['href'], a.next) for a in s.find(text='Format:&nbsp;').parent.findNextSibling('td').findAll('a')]
        media = sorted(media, key=sort_by_dimension, reverse=True)

        # create job to download actual media file
        job = JobInfo.objects.create(func='nasa_download_media', arg=simplejson.dumps(dict(
            record=record.id, url=media[0][0])))
        job.run()

        return record
