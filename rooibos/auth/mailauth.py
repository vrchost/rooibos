from django.contrib.auth.models import User
from django.conf import settings
import imaplib
import poplib
from .baseauth import BaseAuthenticationBackend


class ImapAuthenticationBackend(BaseAuthenticationBackend):
    def authenticate(self, username=None, password=None):
        for imap_auth in settings.IMAP_AUTH:
            imap = None
            try:
                if imap_auth['secure']:
                    imap = imaplib.IMAP4_SSL(
                        imap_auth['server'], imap_auth['port'])
                else:
                    imap = imaplib.IMAP4(
                        imap_auth['server'], imap_auth['port'])
                imap.login(username, password)

                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = self._create_user(
                        username,
                        None,
                        None,
                        username,
                        '%s@%s' % (username, imap_auth['domain'])
                    )
                if not self._post_login_check(user):
                    continue
                return user
            except Exception:
                pass
            finally:
                if imap:
                    imap.shutdown()
        return None


class PopAuthenticationBackend(BaseAuthenticationBackend):
    def authenticate(self, username=None, password=None):
        for pop_auth in settings.POP_AUTH:
            pop = None
            try:
                if pop_auth['secure']:
                    pop = poplib.POP3_SSL(
                        pop_auth['server'], pop_auth['port'])
                else:
                    pop = poplib.POP3(
                        pop_auth['server'], pop_auth['port'])
                pop.user(username)
                pop.pass_(password)

                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = self._create_user(
                        username,
                        None,
                        None,
                        username,
                        '%s@%s' % (username, pop_auth['domain'])
                    )
                if not self._post_login_check(user):
                    continue
                return user
            except Exception:
                pass
            finally:
                if pop:
                    pop.quit()
        return None
