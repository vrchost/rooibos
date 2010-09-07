from django.contrib.auth.models import User
from django.conf import settings
import ldap
from baseauth import BaseAuthenticationBackend

class LdapAuthenticationBackend(BaseAuthenticationBackend):
    def authenticate(self, username=None, password=None):
        for ldap_auth in settings.LDAP_AUTH:
            try:
                username = username.strip()
                l = ldap.initialize(ldap_auth['uri'])
                l.protocol_version = ldap_auth['version']
                for option, value in ldap_auth['options'].iteritems():
                    l.set_option(getattr(ldap, option), value)
                l.simple_bind_s('%s=%s,%s' % (ldap_auth['cn'], username, ldap_auth['base']), password)
                result = l.search_s(ldap_auth['base'],
                                    ldap_auth['scope'],
                                    '%s=%s' % (ldap_auth['cn'], username),
                                    attrlist=ldap_auth['attributes'])
                if (len(result) != 1):
                    continue
                attributes = result[0][1]
                for attr in ldap_auth['attributes']:
                    if not type(attributes[attr]) in (tuple, list):
                        attributes[attr] = (attributes[attr],)
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = self._create_user(username,
                                      None,
                                      ' '.join(attributes[ldap_auth['firstname']]),
                                      ' '.join(attributes[ldap_auth['lastname']]),
                                      attributes[ldap_auth['email']][0])
                if not self._post_login_check(user, attributes):
                    continue
                return user
            except ldap.LDAPError, error_message:
                pass
            finally:
                if l:
                    l.unbind_s()
        return None
