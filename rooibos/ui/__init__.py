
def update_record_selection(request):
    was_selected = map(int, request.POST.getlist('sr'))
    new_selected = map(int, request.POST.getlist('r'))
    selected = list(request.session.get('selected_records', ()))

    remove = [id for id in was_selected if id not in new_selected]
    add = [id for id in new_selected if id not in was_selected]
    map(selected.remove, (id for id in remove if id in selected))
    map(selected.append, (id for id in add if id not in selected))

    request.session['selected_records'] = selected


def clean_record_selection_vars(q):
    q.pop('sr', None)
    q.pop('r', None)
    return q
