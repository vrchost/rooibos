from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def install(request):
    return render(request,
        'mediaviewer_install.html'
    )
