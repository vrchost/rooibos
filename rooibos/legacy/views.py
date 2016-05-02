from django.shortcuts import redirect
from rooibos.viewers.functions import get_viewer_by_name


# Handler for old presentation view URLs
def legacy_viewer(request, record):
    viewer = get_viewer_by_name('presentationviewer')
    return redirect(viewer(None, request, record).url())
