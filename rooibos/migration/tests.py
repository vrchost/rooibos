# from django.test import TestCase
# from management.commands.mdid2migrate import MigrateUsers
#
#
# class UserTestCase(TestCase):
#
#     def test_no_email(self):
#
#         class DummyRow(object):
#             def __init__(self):
#                 self.Login = 'test_UNIQUE98659856298356'
#                 self.Password = None
#                 self.Name = 'Test'
#                 self.FirstName = 'Test'
#                 self.Email = None
#                 self.Administrator = False
#                 self.LastAuthenticated = None
#
#         row = DummyRow()
#         migrate = MigrateUsers(None)
#         user = migrate.create_instance(row)
#         migrate.update(user, row)
#
#         user.save()
