from django.test import TestCase
from rooibos.data.models import Collection
from rooibos.storage.models import Storage
from .models import update_membership_by_attributes, AccessControl, \
    ExtendedGroup, \
    ATTRIBUTE_BASED_GROUP, AUTHENTICATED_GROUP, EVERYBODY_GROUP, \
    join_values, process_shibboleth_attributes
from .functions import check_access, get_effective_permissions, \
    filter_by_access, get_effective_permissions_and_restrictions, \
    add_restriction_precedence
from django.contrib.auth.models import User, Group, AnonymousUser
from django.core.exceptions import PermissionDenied


class AccessTestCase(TestCase):

    def test_get_effective_permissions(self):
        user = User.objects.create(username='test')
        collection = Collection.objects.create()
        self.assertEqual(
            (None, None, None),
            get_effective_permissions(user, collection)
        )

        usergroup1 = Group.objects.create(name='group1')
        usergroup2 = Group.objects.create(name='group2')
        AccessControl.objects.create(
            content_object=collection,
            usergroup=usergroup1,
            read=True,
            write=False,
        )
        AccessControl.objects.create(
            content_object=collection,
            usergroup=usergroup2,
            read=False,
            manage=True,
        )
        self.assertEqual(
            (None, None, None),
            get_effective_permissions(user, collection)
        )

        user.groups.add(usergroup1)
        self.assertEqual(
            (True, False, None),
            get_effective_permissions(user, collection)
        )

        user.groups.add(usergroup2)
        self.assertEqual(
            (False, False, True),
            get_effective_permissions(user, collection)
        )

        AccessControl.objects.create(
            content_object=collection,
            user=user,
            read=True,
            manage=False,
        )
        self.assertEqual(
            (True, None, False),
            get_effective_permissions(user, collection)
        )

    def test_check_access(self):
        user = User.objects.create(username='test2')
        collection = Collection.objects.create()
        self.assertEqual(False, check_access(user, collection, read=True))

        AccessControl.objects.create(
            user=user,
            content_object=collection,
            read=True,
            write=True,
        )

        self.assertTrue(check_access(user, collection, read=True))
        self.assertTrue(check_access(user, collection, read=True, write=True))
        self.assertFalse(
            check_access(user, collection, read=True, manage=True))

        try:
            check_access(
                user, collection, read=True, manage=True, fail_if_denied=True)
            self.assertEqual('result', 'this code should not run')
        except PermissionDenied:
            pass

    def test_filter_by_access_user_only(self):
        user = User.objects.create(username='test3')
        group1 = Collection.objects.create()
        group2 = Collection.objects.create()
        group3 = Collection.objects.create()
        AccessControl.objects.create(
            user=user, content_object=group1, read=True, write=True)
        AccessControl.objects.create(
            user=user, content_object=group2, read=True)
        AccessControl.objects.create(
            user=user, content_object=group3, read=False)

        result = filter_by_access(user, Collection.objects.all())
        self.assertEqual(2, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(False, group3 in result)

        result = filter_by_access(
            user, Collection.objects.all(), read=True, write=True)
        self.assertEqual(1, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(False, group2 in result)
        self.assertEqual(False, group3 in result)

        result = filter_by_access(user, Collection.objects.all(), manage=True)
        self.assertEqual(0, len(result))

    def test_filter_by_access_user_group(self):

        user = User.objects.create(username='test5')
        group1 = Collection.objects.create()
        group2 = Collection.objects.create()
        group3 = Collection.objects.create()
        usergroup1 = Group.objects.create(name='group5a')
        usergroup2 = Group.objects.create(name='group5b')

        user.groups.add(usergroup1)
        user.groups.add(usergroup2)

        # collection 1 permissions
        AccessControl.objects.create(
            user=user, content_object=group1, read=True, write=True)

        # collection 2 permissions
        AccessControl.objects.create(
            user=user, content_object=group2, read=True)
        AccessControl.objects.create(
            usergroup=usergroup1, content_object=group2, write=True)

        # collection 3 permissions
        AccessControl.objects.create(
            user=user, content_object=group3, read=True, manage=False)
        AccessControl.objects.create(
            usergroup=usergroup1,
            content_object=group3,
            read=True,
            write=True,
            manage=True,
        )
        AccessControl.objects.create(
            usergroup=usergroup2,
            content_object=group3,
            write=False,
            manage=False,
        )

        # checks
        result = filter_by_access(user, Collection.objects.all(), read=True)
        self.assertEqual(3, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(True, group3 in result)

        result = filter_by_access(
            user, Collection.objects.all(), read=True, write=True)
        self.assertEqual(2, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(False, group3 in result)

        result = filter_by_access(user, Collection.objects.all(), manage=True)
        self.assertEqual(0, len(result))

    def test_anonymous_user_access_control(self):
        user = AnonymousUser()
        group1 = Collection.objects.create()
        group2 = Collection.objects.create()
        AccessControl.objects.create(content_object=group1, read=True)

        result = filter_by_access(user, Collection.objects.all(), read=True)
        self.assertEqual(1, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(False, group2 in result)

    def test_access_control(self):
        user = User.objects.create(username='test4')
        usergroup = Group.objects.create(name='group4')
        collection = Collection.objects.create()
        Storage.objects.create(name='test4')

        try:
            AccessControl.objects.create(
                user=user, usergroup=usergroup, content_object=collection)
            self.assertEqual('result', 'this code should not run')
        except ValueError:
            pass

    def test_restrictions(self):
        user = User.objects.create(username='test-restr')
        usergroup1 = Group.objects.create(name='group-restr-1')
        usergroup2 = Group.objects.create(name='group-restr-2')
        storage = Storage.objects.create(name='test-restr')
        user.groups.add(usergroup1)
        user.groups.add(usergroup2)

        AccessControl.objects.create(
            usergroup=usergroup1,
            content_object=storage,
            read=True,
            restrictions=dict(width=200, height=200, download='no'),
        )
        AccessControl.objects.create(
            usergroup=usergroup2,
            content_object=storage,
            read=True,
            restrictions=dict(width=300, height=300, download='yes'),
        )

        r, w, m, restrictions = get_effective_permissions_and_restrictions(
            user, storage)
        self.assertEqual(300, restrictions.get('width'))
        self.assertEqual('yes', restrictions.get('download'))

        AccessControl.objects.create(
            user=user,
            content_object=storage,
            read=True,
            restrictions=dict(width=100, height=100),
        )

        r, w, m, restrictions = get_effective_permissions_and_restrictions(
            user, storage)
        self.assertEqual(100, restrictions.get('width'))
        self.assertFalse('download' in restrictions)

    def test_restriction_precendences(self):
        user = User.objects.create(username='test-restrprec')
        usergroup1 = Group.objects.create(name='group-restrprec-1')
        usergroup2 = Group.objects.create(name='group-restrprec-2')
        storage = Storage.objects.create(name='test-restrprec')
        user.groups.add(usergroup1)
        user.groups.add(usergroup2)

        AccessControl.objects.create(
            usergroup=usergroup1,
            content_object=storage,
            read=True,
            restrictions=dict(test='abc'),
        )
        AccessControl.objects.create(
            usergroup=usergroup2,
            content_object=storage,
            read=True,
            restrictions=dict(test='xyz'),
        )

        add_restriction_precedence(
            'test',
            lambda a, b: 'abc' if a == 'abc' or b == 'abc' else 'xyz'
        )
        r, w, m, restrictions = get_effective_permissions_and_restrictions(
            user, storage)
        self.assertEqual('abc', restrictions.get('test'))

        add_restriction_precedence(
            'test',
            lambda a, b: 'xyz' if a == 'xyz' or b == 'xyz' else 'abc'
        )
        r, w, m, restrictions = get_effective_permissions_and_restrictions(
            user, storage)
        self.assertEqual('xyz', restrictions.get('test'))

    def test_no_restrictions_specified(self):
        user = User.objects.create(username='test-norestspec')
        usergroup1 = Group.objects.create(name='group-norestspec-1')
        usergroup2 = Group.objects.create(name='group-norestspec-2')
        storage = Storage.objects.create(name='test-norestspec')
        user.groups.add(usergroup1)
        user.groups.add(usergroup2)

        AccessControl.objects.create(
            usergroup=usergroup1,
            content_object=storage,
            read=True,
            restrictions=dict(width='800', height='800'),
        )
        AccessControl.objects.create(
            usergroup=usergroup2, content_object=storage, read=True)

        r, w, m, restrictions = get_effective_permissions_and_restrictions(
            user, storage)
        self.assertFalse('height' in restrictions)
        self.assertFalse('width' in restrictions)


class ExtendedGroupTestCase(TestCase):

    def test_attribute_based(self):
        usergroup = ExtendedGroup.objects.create(
            name='attrbased-test', type=ATTRIBUTE_BASED_GROUP)
        attribute = usergroup.attribute_set.create(attribute='employeeType')
        attribute.attributevalue_set.create(value='faculty')
        attribute.attributevalue_set.create(value='staff')
        attribute.attributevalue_set.create(value='administrator')

        user = User.objects.create(username='attrbased-testuser-1')
        self.assertFalse(
            usergroup.id in user.groups.all().values_list('id', flat=True))

        update_membership_by_attributes(user, {'employeeType': 'student'})
        self.assertFalse(
            usergroup.id in user.groups.all().values_list('id', flat=True))

        update_membership_by_attributes(
            user, {'employeeType': ['staff', 'student']})
        self.assertTrue(
            usergroup.id in user.groups.all().values_list('id', flat=True))

        update_membership_by_attributes(user, {})
        self.assertFalse(
            usergroup.id in user.groups.all().values_list('id', flat=True))

        attribute2 = usergroup.attribute_set.create(attribute='campus')
        attribute2.attributevalue_set.create(value='harrisonburg')

        update_membership_by_attributes(
            user, {'employeeType': ['staff', 'student']})
        self.assertFalse(
            usergroup.id in user.groups.all().values_list('id', flat=True))

        update_membership_by_attributes(
            user,
            {
                'employeeType': ['staff', 'student'],
                'campus': 'harrisonburg',
                'other': 'some other data'
            }
        )
        self.assertTrue(
            usergroup.id in user.groups.all().values_list('id', flat=True))

    def test_extra_groups(self):
        user = User.objects.create(username='extragroups-testuser-1')
        usergroup = ExtendedGroup.objects.create(
            name='everybody-test', type=EVERYBODY_GROUP)

        groups = ExtendedGroup.objects.get_extra_groups(user)
        self.assertEqual(1, len(groups))
        self.assertTrue(usergroup.id in groups.values_list('id', flat=True))

        anonymous = AnonymousUser()
        authgroup = ExtendedGroup.objects.create(
            name='authgroup-test', type=AUTHENTICATED_GROUP)

        groups = ExtendedGroup.objects.get_extra_groups(user)
        self.assertEqual(2, len(groups))
        self.assertTrue(usergroup.id in groups.values_list('id', flat=True))
        self.assertTrue(authgroup.id in groups.values_list('id', flat=True))

        groups = ExtendedGroup.objects.get_extra_groups(anonymous)
        self.assertEqual(1, len(groups))
        self.assertTrue(usergroup.id in groups.values_list('id', flat=True))
        self.assertFalse(authgroup.id in groups.values_list('id', flat=True))


class ShibbolethAttributesTestCase(TestCase):

    def test_process(self):
        attributes = dict(
            name='John Doe',
            member='staff;alumni;faculty',
        )
        processed = dict(
            (k, join_values(v)) for k, v in attributes.items()
        )

        self.assertEqual('John Doe', processed['name'])
        self.assertTrue(type(processed['member']) is str)
        self.assertTrue(';' not in processed['member'])

        processed = process_shibboleth_attributes(processed)
        self.assertEqual('John Doe', processed['name'])
        self.assertEqual(['staff', 'alumni', 'faculty'], processed['member'])
