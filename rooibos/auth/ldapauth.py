from django.contrib.auth.models import User
from django.conf import settings
import ldap
from .baseauth import BaseAuthenticationBackend
import logging


def d(text):
    return text.decode('utf-8') if type(text) is bytes else text


class LdapAuthenticationBackend(BaseAuthenticationBackend):

    def authenticate(self, username=None, password=None):
        for ldap_auth in settings.LDAP_AUTH:
            l = None
            try:
                username = username.strip()
                l = ldap.initialize(ldap_auth['uri'])
                l.protocol_version = ldap_auth['version']
                for option, value in ldap_auth['options'].items():
                    l.set_option(getattr(ldap, option), value)

                if ldap_auth.get('bind_user'):
                    l.simple_bind_s(
                        ldap_auth['bind_user'],
                        ldap_auth.get('bind_password')
                    )
                    result = l.search_s(
                        ldap_auth['base'],
                        ldap_auth['scope'],
                        '%s=%s' % (ldap_auth['cn'], username),
                        attrlist=[ldap_auth.get('dn', 'dn')]
                    )
                    if len(result) != 1:
                        continue
                    dn = result[0][1].get(
                        ldap_auth.get('dn', 'dn'),
                        # if dn is not returned in attribute list,
                        # use first array element as default
                        result[0][0]
                    )
                    if type(dn) in (tuple, list):
                        dn = dn[0]
                    dn = d(dn)
                else:
                    domain = ldap_auth.get('domain')
                    if domain:
                        dn = '%s@%s' % (username, domain)
                    else:
                        dn = '%s=%s,%s' % (ldap_auth['cn'],
                                           username, ldap_auth['base'])

                l.simple_bind_s(dn, password)
                result = l.search_s(ldap_auth['base'],
                                    ldap_auth['scope'],
                                    '%s=%s' % (ldap_auth['cn'], username),
                                    attrlist=ldap_auth['attributes'])
                # filter results to hits only
                result = [r[1] for r in result if r[0]]
                if len(result) != 1:
                    continue
                attributes = result[0]
                for attr in ldap_auth['attributes']:
                    if attr in attributes:
                        if not type(attributes[attr]) in (tuple, list):
                            attributes[attr] = (attributes[attr],)
                    else:
                        attributes[attr] = []

                # fetch membership in specified groups
                attributes['_groups'] = []
                for group in ldap_auth.get('groups', ()):
                    result = l.search_s(
                        ldap_auth['base'],
                        ldap_auth['scope'],
                        '(&(objectClass=user)(%s=%s)(memberof=%s))' % (
                            ldap_auth['cn'], username, group
                        ),
                    )
                    if len(result) == 1:
                        attributes['_groups'].append(group)

                # process Django user
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    emails = attributes[ldap_auth['email']]
                    if not emails:
                        email = ldap_auth.get(
                            'email_default', '%s@unknown') % username
                    else:
                        email = emails[0]
                    user = self._create_user(
                        username,
                        None,
                        ' '.join(d(a) for a in attributes[ldap_auth['firstname']]),
                        ' '.join(d(a) for a in attributes[ldap_auth['lastname']]),
                        d(email)
                    )
                if not self._post_login_check(user, attributes):
                    continue
                return user
            except ldap.LDAPError as error_message:
                logging.debug('LDAP error: %s' % error_message)
            finally:
                if l:
                    l.unbind_s()
        return None
