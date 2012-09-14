from rooibos.util import json_view
from rooibos.data.models import Record
from functions import get_markers


@json_view
def set_marker(request, id, name):
    if request.method == "POST":
        index = request.POST['index']
        time = request.POST['time']
        if index and time:
            record = Record.filter_one_by_access(request.user, id)
            can_edit = record.editable_by(request.user)
            markers = get_markers(record)
            m = dict(map(lambda v: v.split(','), markers.value.split())) if markers.value else dict()
            m[index] = time
            to_remove = []
            prev_val = None
            for key in sorted(m.keys()):
                if prev_val:
                    if prev_val >= m[key]:
                        to_remove.append(key)
                else:
                    prev_val = m[key]
            for key in to_remove:
                del m[key]
            markers.value = '\n'.join('%s,%s' % (v,k) for v,k in m.iteritems())
            markers.save()
            return dict(message="Marker saved.")
        else:
            return dict(result="Error", message="Missing parameters")
    else:
        return dict(result="Error", message="Invalid method. Use POST.")
