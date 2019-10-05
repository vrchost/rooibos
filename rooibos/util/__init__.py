from django.http import HttpResponse
import json as simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
from django.utils.decorators import wraps
from django.utils.functional import SimpleLazyObject
from django.db.models import Q
import sys
import mimetypes
import logging
import os
import hashlib


# Decorator to solve issues with IE/SSL/Flash caching
def must_revalidate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        # "no-cache, must-revalidate, no-store"
        response["Cache-Control"] = "bogus"
        # "no-cache"
        response["Pragma"] = "bogus"
        return response
    return wrapper


def json_view(func):
    # http://www.djangosnippets.org/snippets/622/
    def wrap(request, *a, **kw):
        response = None
        try:
            func_val = func(request, *a, **kw)
            assert isinstance(func_val, dict)
            response = dict(func_val)
            if 'result' not in response:
                response['result'] = 'ok'
        except KeyboardInterrupt:
            # Allow keyboard interrupts through for debugging.
            raise
        except Exception as e:
            # Mail the admins with the error
            exc_info = sys.exc_info()
            subject = 'JSON view error: %s' % request.path
            try:
                request_repr = repr(request)
            except:
                request_repr = 'Request repr() unavailable'
            import traceback
            message = 'Traceback:\n%s\n\nRequest:\n%s' % (
                '\n'.join(traceback.format_exception(*exc_info)),
                request_repr,
            )
            mail_admins(subject, message, fail_silently=True)
            logging.error(message)

            # Come what may, we're returning JSON.
            if hasattr(e, 'message'):
                msg = e.message
            else:
                msg = _('Internal error') + ': ' + str(e)
            response = {'result': 'error',
                        'text': msg}

        json = simplejson.dumps(response)
        # mimetype='application/json'
        return HttpResponse(json, content_type='text/plain')
    return wrap


def unique_slug(item, slug_source=None, slug_literal=None, slug_field='name',
                id_field='id', check_current_slug=False):
    """Ensures a unique slug field by appending an integer counter to duplicate
    slugs.

    Source: http://www.djangosnippets.org/snippets/512/
    Modified by Andreas Knab, 10/14/2008

    The item's slug field is first prepopulated by slugify-ing the source
    field.
    If that value already exists, a counter is appended to the slug, and the
    counter incremented upward until the value is unique.

    For instance, if you save an object titled Daily Roundup, and the slug
    daily-roundup is already taken, this function will try daily-roundup-2,
    daily-roundup-3, daily-roundup-4, etc, until a unique value is found.

    Call from within a model's custom save() method like so:
    unique_slug(item, slug_source='field1', slug_field='field2')
    where the value of field slug_source will be used to prepopulate the value
    of slug_field.

    If slug_source does not exist, it will be used as a literal string.
    """
    if check_current_slug or not getattr(item, slug_field) or \
            not getattr(item, id_field):
        # if it's already got a slug, do nothing.
        from django.template.defaultfilters import slugify
        item_model = item.__class__
        max_length = item_model._meta.get_field(slug_field).max_length
        if check_current_slug and getattr(item, slug_field):
            slug = slugify(getattr(item, slug_field))
        else:
            slug = slugify(
                slug_source and
                getattr(item, slug_source, slug_literal) or
                slug_literal
            )
        slug = slug[:max_length]
        slug_check = slug[:min(len(slug), max_length - len(str(sys.maxsize)))]

        query = item_model.objects.complex_filter(
            {'%s__startswith' % slug_field: slug_check})

        # check to see if slug needs to be unique together
        # with another field only
        unique_together = [f for f in item_model._meta.unique_together if slug_field in f]
        # only handle simple case of one unique_together with
        # one additional field
        if len(unique_together) == 1 and len(unique_together[0]) == 2:
            l = list(unique_together[0])
            l.remove(slug_field)
            unique_with = l[0]
            query = query & item_model.objects.complex_filter(
                {unique_with: getattr(item, unique_with)})

        # don't find ourselves to avoid conflict if our slug is already
        # the same
        if getattr(item, id_field):
            query = query & item_model.objects.complex_filter(
                ~Q(**{id_field: getattr(item, id_field)}))

        all_slugs = [getattr(i, slug_field) for i in query]

        if slug in all_slugs:
            counter = 2
            uniqueslug = slug
            while uniqueslug in all_slugs:
                uniqueslug = "%s-%i" % (
                    slug[:max_length - 1 - len(str(counter))], counter)
                counter += 1
            slug = uniqueslug
        setattr(item, slug_field, slug)


def safe_int(value, default):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def guess_extension(mimetype):
    x = mimetypes.guess_extension(mimetype)
    if x == '.jpe':
        return '.jpeg'
    return x


def xfilter(func, iterator):
    """Iterative version of builtin 'filter'."""
    iterator = iter(iterator)
    while 1:
        next = next(iterator)
        if func(next):
            yield next


def create_link(file, link, hard=False):
    func = 'link' if hard else 'symlink'
    if hasattr(os, func):
        # Linux, use built-in function
        try:
            getattr(os, func)(file, link)
            return True
        except OSError:
            return False
    else:
        # Windows, use mklink
        return 0 == os.system("mklink %s \"%s\" \"%s\"" %
                              ('/H' if hard else '', link, file))


def calculate_hash(*args):
    hash = hashlib.md5()
    for arg in args:
        hash.update(repr(arg).encode('utf8', errors='ignore'))
    return hash.hexdigest()


class IterableLazyObject(SimpleLazyObject):

    def __iter__(self):
        if self._wrapped is None:
            self._setup()
        return self._wrapped.__iter__()
