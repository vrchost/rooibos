from django.conf.urls import url
from .views import manage_collections, manage_collection, record_preview, \
    record, record_delete, data_import_file, data_import, \
    save_collection_visibility_preferences, collection_dump_view


urlpatterns = [
    url(
        r'^collections/manage/$',
        manage_collections,
        name='data-collections-manage'
    ),
    url(r'^collection/new/$', manage_collection, name='data-collection-new'),
    url(
        r'^collection/(?P<id>\d+)/(?P<name>[-\w]+)/manage/$',
        manage_collection,
        name='data-collection-manage'
    ),
    url(r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/$', record, name='data-record'),
    url(
        r'^record-preview/(?P<id>\d+)/$',
        record_preview,
        name='data-record-preview'
    ),
    # The following URL is to get the correct prefix for all record URLs
    url(
        r'^record/$',
        lambda request: None,
        name='data-record-back-helper-url'
    ),
    url(
        r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/edit/$',
        record,
        kwargs={'edit': True},
        name='data-record-edit'
    ),
    url(
        r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/delete/$',
        record_delete,
        name='data-record-delete'
    ),
    url(
        r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/edit/(?P<contexttype>\w+\.\w+)/'
        r'(?P<contextid>\d+)/(?P<contextname>[-\w]+)/$',
        record,
        kwargs={'edit': True},
        name='data-record-edit-context'
    ),
    url(
        r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/edit/customize/$',
        record,
        kwargs={'edit': True, 'customize': True},
        name='data-record-edit-customize'
    ),
    url(
        r'^record/new/$',
        record,
        kwargs={'id': None, 'name': None, 'edit': True},
        name='data-record-new'
    ),
    url(
        r'^record/copy/(?P<copyid>\d+)/(?P<copyname>[-\w]+)/$',
        record,
        kwargs={'id': None, 'name': None, 'edit': True, 'copy': True},
        name='data-record-copy'
    ),
    url(
        r'^record/new/personal/$',
        record,
        kwargs={'id': None, 'name': None, 'edit': True, 'personal': True},
        name='data-record-new-personal'
    ),
    url(r'^import/$', data_import, name='data-import'),
    url(
        r'^import/(?P<file>[\w\d]{32})/$',
        data_import_file,
        name='data-import-file'
    ),
    url(
        r'^collection-visibility-preferences/save/$',
        save_collection_visibility_preferences,
        name='data-save-collection-visibility-preferences'
    ),
    url(
        r'^collection/(?P<identifier>\d+)/(?P<name>[-\w]+)/dump/$',
        collection_dump_view,
        name='data-collection-dump'
    ),
]
