from django.conf.urls import url
from django.views.generic.base import TemplateView
from .views import css, select_record, add_tags, remove_tag, manage, options, \
    clear_selected_records, delete_selected_records, \
    AnnouncementCreateView, AnnouncementUpdateView, AnnouncementDeleteView


urlpatterns = [
    url(r'^css/(?P<stylesheet>[-\w]+)/$', css, name='ui-css'),
    url(r'^api/select-record/', select_record, name='ui-api-select-record'),
    url(r'^tag/(?P<type>\d+)/(?P<id>\d+)/', add_tags, name='ui-add-tags'),
    url(
        r'^tag/remove/(?P<type>\d+)/(?P<id>\d+)/',
        remove_tag,
        name='ui-remove-tag'
    ),
    url(r'^manage/$', manage, name='ui-management'),
    url(r'^options/$', options, name='ui-options'),
    url(
        r'^clear-selected/$',
        clear_selected_records,
        name='ui-clear-selected'
    ),
    url(
        r'^delete-selected/$',
        delete_selected_records,
        name='ui-delete-selected'
    ),
    url(
        r'^report-problem/$',
        TemplateView.as_view(template_name='ui_report_problem.html'),
        name='ui-report-problem'
    ),
    url(
        r'^announcement/new/$',
        AnnouncementCreateView.as_view(),
        name='ui-announcement-new'
    ),
    url(
        r'^announcement/(?P<pk>\d+)/edit/$',
        AnnouncementUpdateView.as_view(),
        name='ui-announcement-edit'
    ),
    url(
        r'^announcement/(?P<pk>\d+)/delete/$',
        AnnouncementDeleteView.as_view(),
        name='ui-announcement-delete'
    ),
]
