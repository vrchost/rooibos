from django.test import TestCase
from django.contrib.auth.models import User, Group
from .management.commands.managegroup import Command


class TestManageGroupCommand(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(
            username='TestManageGroupCommand-user1')
        self.user2 = User.objects.create(
            username='TestManageGroupCommand-user2')
        self.user3 = User.objects.create(
            username='TestManageGroupCommand-user3')
        self.newusername = 'TestManageGroupCommand-newuser'

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

    def test_no_parameters(self):
        output = []
        Command().handle(output=output)
        self.assertEqual(1, len(output))

    def test_simple_group(self):
        output = []
        group = Group.objects.filter(name='test_simple_group')
        self.assertEqual(0, len(group))
        Command().handle(usergroup='test_simple_group', output=output)
        group = Group.objects.filter(name='test_simple_group')
        self.assertEqual(1, len(group))
        self.assertEqual(0, len(output))

    def test_simple_group_members(self):
        output = []
        group = Group.objects.create(name='test_simple_group_members')
        group.user_set.add(self.user1)
        group.user_set.add(self.user3)
        Command().handle(
            usergroup='test_simple_group_members',
            users=','.join(
                [self.user1.username, self.user2.username,
                 'this-user-does-not-exist']),
            output=output
        )
        self.assertEqual(2, len(group.user_set.all()))
        self.assertEqual(1, len(output))

    def test_add_group_members(self):
        output = []
        group = Group.objects.create(name='test_add_group_members')
        group.user_set.add(self.user1)
        Command().handle(usergroup='test_add_group_members',
                         addusers=[self.user1.username, self.user3.username],
                         output=output)
        self.assertEqual(2, len(group.user_set.all()))
        self.assertEqual(0, len(output))
        Command().handle(
            usergroup='test_add_group_members',
            addusers=[','.join([self.user2.username, self.user3.username])],
            output=output)
        self.assertEqual(3, len(group.user_set.all()))
        self.assertEqual(0, len(output))

    def test_remove_group_members(self):
        output = []
        group = Group.objects.create(name='test_remove_group_members')
        group.user_set.add(self.user1)
        group.user_set.add(self.user2)
        Command().handle(
            usergroup='test_remove_group_members',
            removeusers=[self.user1.username, self.user3.username],
            output=output)
        self.assertEqual(1, len(group.user_set.all()))
        self.assertEqual(0, len(output))

    def test_create_users(self):
        output = []
        group = Group.objects.create(name='test_create_users')
        self.assertEqual(0, User.objects.filter(
            username=self.newusername).count())
        Command().handle(
            usergroup='test_create_users',
            addusers=['%s:test@example.com:John:Doe:changeme' %
                      self.newusername],
            createusers=True,
            output=output)
        self.assertEqual(1, len(group.user_set.all()))
        users = User.objects.filter(username=self.newusername)
        self.assertEqual(1, users.count())
        self.assertEqual('John', users[0].first_name)
        self.assertEqual('Doe', users[0].last_name)
        self.assertEqual('test@example.com', users[0].email)
        self.assertEqual(0, len(output))
