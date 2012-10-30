from django.contrib.auth.models import User
from django.conf import settings
import ldap
from baseauth import BaseAuthenticationBackend
import logging

class LdapAuthenticationBackend(BaseAuthenticationBackend):
    def authenticate(self, username=None, password=None):
        for ldap_auth in settings.LDAP_AUTH:
            try:
                username = username.strip()
                l = ldap.initialize(ldap_auth['uri'])
                l.protocol_version = ldap_auth['version']
                for option, value in ldap_auth['options'].iteritems():
                    l.set_option(getattr(ldap, option), value)

                if ldap_auth.get('bind_user'):
                    l.simple_bind_s(ldap_auth['bind_user'],
                                    ldap_auth.get('bind_password'))
                    result = l.search_s(ldap_auth['base'],
                                    ldap_auth['scope'],
                                    '%s=%s' % (ldap_auth['cn'], username),
                                    attrlist=[ldap_auth.get('dn', 'dn')])
                    if (len(result) != 1):
                        continue
                    dn = result[0][1].get(ldap_auth.get('dn', 'dn'))
                    if type(dn) in (tuple, list):
                        dn = dn[0]
                else:
                    dn = '%s=%s,%s' % (ldap_auth['cn'],
                                       username, ldap_auth['base'])

                l.simple_bind_s(dn, password)
                result = l.search_s(ldap_auth['base'],
                                    ldap_auth['scope'],
                                    '%s=%s' % (ldap_auth['cn'], username),
                                    attrlist=ldap_auth['attributes'])
                if (len(result) != 1):
                    continue
                attributes = result[0][1]
                for attr in ldap_auth['attributes']:
                    if attributes.has_key(attr):
                        if not type(attributes[attr]) in (tuple, list):
                            attributes[attr] = (attributes[attr],)
                    else:
                        attributes[attr] = []
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
                logging.debug('LDAP error: %s' % error_message)
            finally:
                if l:
                    l.unbind_s()
        return None
