from django.test import TestCase
from django.contrib.auth.models import User

from .models import UserProfile
from .views import store_settings, load_settings


class UserProfileTest(TestCase):

    def test_duplicate_key(self):

        user = User.objects.create(username='UserProfileTest-1')
        profile = UserProfile.objects.create(user=user)
        profile.preferences.create(setting='duplicate', value='test1')
        profile.preferences.create(setting='duplicate', value='test2')

        store_settings(user, 'duplicate', 'test3')

        settings = load_settings(user, 'duplicate')

        self.assertEqual(['test3'], settings['duplicate'])
