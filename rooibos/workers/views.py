from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from .models import OwnedTaskResult
from .tasks import testjob, _get_scratch_dir
import os


@login_required
def joblist(request):

    jobs = OwnedTaskResult.objects.all()
    if not request.user.is_superuser:
        jobs = jobs.filter(owner=request.user)
    jobs = jobs.order_by('-date_done')

    if request.method == "POST":
        if request.POST.get('remove'):
            ids = request.POST.getlist('r')
            if not request.user.is_superuser:
                jobs = jobs.exclude(status='PROGRESS')
            jobs.filter(id__in=ids).delete()
        elif request.POST.get('testjob'):
            testjob.delay(owner=request.user.id)

        return HttpResponseRedirect(request.get_full_path())

    highlight = request.GET.get('highlight')

    return render_to_response("workers_jobs.html",
                              {'jobs': jobs,
                               'highlight': highlight,
                               },
                              context_instance=RequestContext(request))


@login_required
def download_attachment(request, url):
    attachment = os.path.join(_get_scratch_dir(), url)
    retval = HttpResponse(content=open(attachment, 'rb'))
    retval["Content-Disposition"] = \
            'attachment; filename="%s"' % url
    return retval
