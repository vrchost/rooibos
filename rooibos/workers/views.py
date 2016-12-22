from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django_celery_results.models import TaskResult
from .tasks import testjob


@login_required
def joblist(request):

    jobs = TaskResult.objects.all()
    if not request.user.is_superuser:
        jobs = jobs.filter(taskownership__owner=request.user)
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

    try:
        highlight = int(request.GET.get('highlight'))
    except (ValueError, TypeError):
        highlight = None

    return render_to_response("workers_jobs.html",
                              {'jobs': jobs,
                               'highlight': highlight,
                               },
                              context_instance=RequestContext(request))
