from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import _get_queryset


def get_accesscontrols_for_object(model_instance):
    from models import AccessControl
    model_type = ContentType.objects.get_for_model(model_instance)
    aclist = AccessControl.objects.select_related('user', 'usergroup').filter(object_id=model_instance.id, content_type__pk=model_type.id).order_by('usergroup__name', 'user__username')
    return aclist


def get_effective_permissions_and_restrictions(user, model_instance):
    from models import AccessControl, ExtendedGroup
    user = user or AnonymousUser()
    if user.is_superuser:
        return (True, True, True, None)
    owner = getattr(model_instance, 'owner', None)
    if owner and owner == user:
        return (True, True, True, None)
    if not user.is_anonymous():
        q = Q(user=user) | Q(usergroup__in=ExtendedGroup.objects.get_extra_groups(user)) | Q(usergroup__in=user.groups.all())
    else:
        q = Q(usergroup__in=ExtendedGroup.objects.get_extra_groups(user)) | Q(user=None, usergroup=None)
    model_type = ContentType.objects.get_for_model(model_instance)
    aclist = AccessControl.objects.filter(q, object_id=model_instance.id, content_type__pk=model_type.id)

    def reduce_by_filter(f):
        def combine(a, b):
            if a == False or (a == True and b == None): return a
            else: return b
        read = write = manage = None
        restrictions = dict()
        for ac in filter(f, aclist):
            read = combine(ac.read, read)
            write = combine(ac.write, write)
            manage = combine(ac.manage, manage)
            if ac.restrictions:
                for k, v in ac.restrictions.iteritems():
                    if not restrictions.has_key(k) or restrictions[k] > v:
                        restrictions[k] = v;
        return (read, write, manage, restrictions)

    (gr, gw, gm, restrictions) = reduce_by_filter(lambda a: a.usergroup)
    (ur, uw, um, urestrictions) = reduce_by_filter(lambda a: a.user)

    restrictions.update(urestrictions)

    return (ur or (ur == None and gr),
            uw or (uw == None and gw),
            um or (um == None and gm),
            restrictions or None)


def get_effective_permissions(user, model_instance):
    return get_effective_permissions_and_restrictions(user, model_instance)[:3]


def check_access(user, model_instance, read=True, write=False, manage=False, fail_if_denied=False):
    (r, w, m) = get_effective_permissions(user, model_instance)
    if (read and not r) or (write and not w) or (manage and not m):
        if fail_if_denied:
            raise PermissionDenied
        return False
    return True


def filter_by_access(user, queryset, read=True, write=False, manage=False):
    from models import AccessControl, ExtendedGroup
    user = user or AnonymousUser()
    queryset = _get_queryset(queryset)
    if not (read or write or manage) or user.is_superuser:  # nothing to do
        return queryset
    model_type = ContentType.objects.get_for_model(queryset.model)
    usergroups_q = Q(usergroup__in=ExtendedGroup.objects.get_extra_groups(user))
    if not user.is_anonymous():
        usergroups_q = usergroups_q | Q(usergroup__in=user.groups.all())
    user_q = Q(user__isnull=True, usergroup__isnull=True) if user.is_anonymous() else Q(user=user)
    owner_q = Q(owner=user) if 'owner' in (f.name for f in queryset.model._meta.fields) and not user.is_anonymous() else None

    def build_query(**kwargs):
        (field, check) = kwargs.popitem()
        if not check:
            return Q()
        user_allowed_q = Q(id__in=AccessControl.objects.filter(user_q, content_type__id=model_type.id,
                                                               **{field: True}).values('object_id'))
        user_denied_q = Q(id__in=AccessControl.objects.filter(user_q, content_type__id=model_type.id,
                                                              **{field: False}).values('object_id'))
        group_allowed_q = Q(id__in=AccessControl.objects.filter(usergroups_q, content_type__id=model_type.id,
                                                                **{field: True}).values('object_id'))
        group_denied_q = Q(id__in=AccessControl.objects.filter(usergroups_q, content_type__id=model_type.id,
                                                               **{field: False}).values('object_id'))
        result = ((group_allowed_q & ~group_denied_q) | user_allowed_q) & ~user_denied_q
        if owner_q:
            result = owner_q | result
        return result

    return queryset.filter(build_query(read=read), build_query(write=write), build_query(manage=manage)).distinct()


def accessible_ids(user, queryset, read=True, write=False, manage=False):
    queryset = _get_queryset(queryset)
    return filter_by_access(user, queryset, read, write, manage).values('id')


def accessible_ids_list(user, queryset, read=True, write=False, manage=False):
    queryset = _get_queryset(queryset)
    return filter_by_access(user, queryset, read, write, manage).values_list('id', flat=True)


def sync_access(from_instance, to_instance):
    from models import AccessControl
    from_model_type = ContentType.objects.get_for_model(from_instance)
    to_model_type = ContentType.objects.get_for_model(to_instance)
    AccessControl.objects.filter(content_type=to_model_type, object_id=to_instance.id).delete()
    for ac in AccessControl.objects.filter(content_type=from_model_type, object_id=from_instance.id):
        AccessControl.objects.create(content_type=to_model_type,
                                     object_id=to_instance.id,
                                     user=ac.user,
                                     usergroup=ac.usergroup,
                                     read=ac.read,
                                     write=ac.write,
                                     manage=ac.manage,
                                     restrictions_repr=ac.restrictions_repr)
