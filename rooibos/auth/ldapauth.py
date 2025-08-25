from django.contrib.auth.models import User
from django.conf import settings
import ldap
from .baseauth import BaseAuthenticationBackend
import logging


def d(text):
    return text.decode('utf-8') if isinstance(text, bytes) else text


class LdapAuthenticationBackend(BaseAuthenticationBackend):

    def authenticate(self, request=None, username=None, password=None):
        for ldap_auth in settings.LDAP_AUTH:
            conn = None
            try:
                username = username.strip()
                logging.info(f"LDAP: Connecting to {ldap_auth['uri']}")

                # Initialize LDAP connection
                conn = ldap.initialize(ldap_auth['uri'])
                conn.protocol_version = ldap_auth['version']
                for option, value in ldap_auth['options'].items():
                    conn.set_option(getattr(ldap, option), value)

                # -----------------------------
                # If we have a bind_user → fetch attrs before user bind
                # -----------------------------
                if ldap_auth.get('bind_user'):
                    logging.info("LDAP: Binding as service account")
                    conn.simple_bind_s(
                        ldap_auth['bind_user'],
                        ldap_auth.get('bind_password')
                    )

                    # Fetch full user entry (DN + all attributes)
                    search_filter = f"{ldap_auth['cn']}={username}"
                    search_attrs = list(ldap_auth['attributes']) + [ldap_auth.get('dn', 'dn')]

                    logging.info(f"LDAP: Searching {ldap_auth['base']} for {search_filter} with attrs {search_attrs}")
                    result = conn.search_s(
                        ldap_auth['base'],
                        ldap_auth['scope'],
                        search_filter,
                        attrlist=search_attrs
                    )

                    if len(result) != 1:
                        logging.warning("LDAP: Did not find exactly one user entry")
                        continue

                    dn = result[0][0]  # distinguishedName
                    attributes = result[0][1]

                    # Normalize attributes like old version
                    for attr in ldap_auth['attributes']:
                        if attr in attributes:
                            if not isinstance(attributes[attr], (tuple, list)):
                                attributes[attr] = (attributes[attr],)
                            attributes[attr] = [d(a) for a in attributes[attr]]
                        else:
                            attributes[attr] = []

                    # Validate user credentials by binding as them
                    logging.info(f"LDAP: Validating password by binding dn={dn}")
                    conn.simple_bind_s(dn, password)

                # -----------------------------
                # Else: No bind_user → bind user directly, then fetch attrs
                # -----------------------------
                else:
                    domain = ldap_auth.get('domain')
                    if domain:
                        dn = f"{username}@{domain}"
                    else:
                        dn = f"{ldap_auth['cn']}={username},{ldap_auth['base']}"

                    logging.info(f"LDAP: Direct user bind dn={dn}")
                    conn.simple_bind_s(dn, password)

                    # Fetch attributes after bind
                    search_filter = f"{ldap_auth['cn']}={username}"
                    logging.info(f"LDAP: Searching for attributes after bind")
                    result = conn.search_s(
                        ldap_auth['base'],
                        ldap_auth['scope'],
                        search_filter,
                        attrlist=list(ldap_auth['attributes'])
                    )

                    if len(result) != 1:
                        continue

                    attributes = result[0][1]
                    for attr in ldap_auth['attributes']:
                        if attr in attributes:
                            if not isinstance(attributes[attr], (tuple, list)):
                                attributes[attr] = (attributes[attr],)
                            attributes[attr] = [d(a) for a in attributes[attr]]
                        else:
                            attributes[attr] = []

                # -----------------------------
                # Fetch group membership if defined
                # -----------------------------
                attributes['_groups'] = []
                for group in ldap_auth.get('groups', ()):
                    group_search_filter = f"(&(objectClass=user)({ldap_auth['cn']}={username})(memberof={group}))"
                    group_result = conn.search_s(
                        ldap_auth['base'],
                        ldap_auth['scope'],
                        group_search_filter,
                    )
                    if len(group_result) == 1:
                        attributes['_groups'].append(group)

                # -----------------------------
                # Process Django user object
                # -----------------------------
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    emails = attributes.get(ldap_auth['email'], [])
                    if not emails:
                        email = ldap_auth.get('email_default', f"{username}@unknown")
                    else:
                        email = emails[0]

                    firstname = " ".join(attributes.get(ldap_auth['firstname'], []))
                    lastname = " ".join(attributes.get(ldap_auth['lastname'], []))

                    user = self._create_user(
                        username,
                        None,
                        firstname,
                        lastname,
                        d(email)
                    )

                # Post-login checks
                if not self._post_login_check(user, attributes):
                    continue

                return user

            except ldap.LDAPError as error_message:
                logging.exception(f"LDAP error: {error_message}")
            except Exception:
                logging.exception("Exception in LDAP auth")
            finally:
                if conn:
                    conn.unbind_s()

        return None
