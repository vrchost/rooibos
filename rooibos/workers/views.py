from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from models import JobInfo

@login_required
def joblist(request):

    if request.user.is_superuser:
        jobs = JobInfo.objects.all()
    else:
        jobs = JobInfo.objects.filter(owner=request.user)

    if request.method == "POST":
        if request.POST.get('remove'):
            ids = request.POST.getlist('r')
            if not request.user.is_superuser:
                jobs = jobs.filter(completed=True)
            jobs.filter(id__in=ids).delete()
        elif request.POST.get('testjob'):
            JobInfo.objects.create(
                owner=request.user,
                func='testjob',
            ).run()
        else:
            for k, v in request.POST.iteritems():
                if k.startswith('run-'):
                    JobInfo.objects.get(id=k[4:]).run()

        return HttpResponseRedirect(request.get_full_path())

    try:
        highlight = int(request.GET.get('highlight'))
    except (ValueError, TypeError):
        highlight = None

    return render_to_response("workers_jobs.html",
                              {'jobs': jobs,
                               'highlight': highlight,
                               },
                              context_instance=RequestContext(request))
