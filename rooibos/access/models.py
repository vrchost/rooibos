from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User, Group
from ipaddr import IPAddress, IPNetwork


class AccessControl(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, null=True, blank=True)
    usergroup = models.ForeignKey(Group, null=True, blank=True)
    read = models.NullBooleanField()
    write = models.NullBooleanField()
    manage = models.NullBooleanField()
    restrictions_repr = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('content_type', 'object_id', 'user', 'usergroup')
        app_label = 'access'

    def save(self, **kwargs):
        if (self.user and self.usergroup):
            raise ValueError("Mutually exclusive fields set")
        super(AccessControl, self).save(kwargs)

    def __str__(self):
        def f(flag, char):
            if flag is True:
                return char
            elif flag is False:
                return char.upper()
            else:
                return '-'

        return '%s [%s%s%s] %s (%s)' % (
            self.user or self.usergroup or 'AnonymousUser',
            f(self.read, 'r'),
            f(self.write, 'w'),
            f(self.manage, 'm'),
            self.content_object,
            self.content_type
        )

    def restrictions_get(self):
        if self.restrictions_repr:
            return eval(self.restrictions_repr, {"__builtins__": None}, {})
        else:
            return None

    def restrictions_set(self, value):
        if value:
            self.restrictions_repr = repr(value)
        else:
            self.restrictions_repr = ''

    restrictions = property(restrictions_get, restrictions_set)


EVERYBODY_GROUP = 'E'
AUTHENTICATED_GROUP = 'A'
IP_BASED_GROUP = 'I'
ATTRIBUTE_BASED_GROUP = 'P'


def update_membership_by_attributes(user, info):
    for group in ExtendedGroup.objects.filter(type=ATTRIBUTE_BASED_GROUP):
        group.update_membership_by_attributes(user, info)
    return True


class ExtendedGroupManager(models.Manager):

    def get_extra_groups(self, user, assume_authenticated=False):
        # retrieve membership in special groups such as everyone and
        # authenticated users membership for those types of groups
        # is not stored explicitly
        q = Q(type=EVERYBODY_GROUP)
        if assume_authenticated or user.is_authenticated():
            q = q | Q(type=AUTHENTICATED_GROUP)
        ip_group_memberships = getattr(
            user, '_cached_ip_group_memberships', [])
        if ip_group_memberships:
            q = q | Q(id__in=ip_group_memberships)
        return self.filter(q)


class ExtendedGroup(Group):
    TYPE_CHOICES = (
        ('A', 'Authenticated'),
        ('I', 'IP Address based'),
        ('P', 'Attribute based'),
        ('E', 'Everybody'),
    )

    class Meta:
        app_label = 'access'

    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    objects = ExtendedGroupManager()

    # to be called upon a user login
    def update_membership_by_attributes(self, user, info=None):
        if self.type == ATTRIBUTE_BASED_GROUP:
            if info and self._check_attributes(info):
                self.user_set.add(user)
            else:
                self.user_set.remove(user)

    def _check_subnet(self, address):
        ip = IPAddress(address)
        for subnet in self.subnet_set.values_list('subnet', flat=True):
            if ip in IPNetwork(subnet):
                return True
        return False

    def _check_attributes(self, attributes):
        for attribute in Attribute.objects.filter(group=self):
            values = attributes.get(attribute.attribute, [])
            for value in attribute.attributevalue_set.all().values_list(
                    'value', flat=True):
                if (hasattr(values, '__iter__')
                        and not isinstance(values, str)
                        and value in values
                    ) or value == values:
                    break
            else:
                return False
        return True

    def _full_type(self):
        return [a_f for a_f in self.TYPE_CHOICES if a_f[0] == self.type][0][1]

    def __str__(self):
        return '%s (%s)' % (self.name, self._full_type())


class Subnet(models.Model):
    group = models.ForeignKey(ExtendedGroup, limit_choices_to={'type': 'I'})
    subnet = models.CharField(max_length=80)

    def __str__(self):
        return '%s: %s' % (self.group.name, self.subnet)

    class Meta:
        app_label = 'access'


class Attribute(models.Model):
    group = models.ForeignKey(ExtendedGroup, limit_choices_to={'type': 'P'})
    attribute = models.CharField(max_length=255)

    def __str__(self):
        return '%s: %s' % (self.group.name, self.attribute)

    class Meta:
        app_label = 'access'


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute)
    value = models.CharField(max_length=255)

    class Meta:
        app_label = 'access'


SEPARATOR = ' :: '


def join_values(values):
    return SEPARATOR.join(values.split(';'))


def split_values(values):
    if values and SEPARATOR in values:
        return values.split(SEPARATOR)
    else:
        return values


def process_shibboleth_attributes(attributes):
    """
    django-shibboleth only supports single value attributes, so
    attribute lists are converted to single values before submitting
    them to django-shibboleth.
    :return: dict of attributes with value lists converted to single values
    """
    return dict((attribute, split_values(values))
                for attribute, values in attributes.items())


def post_shibboleth_login(sender, **kwargs):
    user = kwargs.get('user')
    shib_attrs = kwargs.get('shib_attrs')
    if user and shib_attrs:
        # django-shibboleth only supports single value attributes, so
        # attribute lists are converted to single values before submitting
        # them to django-shibboleth.  Afterwards we have to convert them
        # back here
        attributes = process_shibboleth_attributes(shib_attrs)
        update_membership_by_attributes(user, attributes)


# Signal handlers for Shibboleth

try:
    from django_shibboleth.signals import shib_logon_done

    shib_logon_done.connect(post_shibboleth_login,
                            dispatch_uid='post_shibboleth_login')
except ImportError:
    pass
