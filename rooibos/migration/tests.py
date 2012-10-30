import unittest
from management.commands.mdid2migrate import MigrateUsers


class UserTestCase(unittest.TestCase):

    def testNoEmail(self):

        class DummyRow(object):
            def __init__(self):
                self.Login = 'test'
                self.Password = None
                self.Name = 'Test'
                self.FirstName = 'Test'
                self.Email = None
                self.Administrator = False
                self.LastAuthenticated = None

        row = DummyRow()
        migrate = MigrateUsers(None)
        user = migrate.create_instance(row)
        migrate.update(user, row)

        user.save()
