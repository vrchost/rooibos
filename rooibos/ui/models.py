from django.db.models import signals
from django.contrib.sites import models as sites_app
from django.contrib.flatpages import models as flatpages_app
from django.contrib.auth import models as auth_app


def create_site_flatpage_fixtures(*args, **kwargs):
    print("Creating sites fixtures")
    sites_app.Site.objects.get_or_create(
        domain='localhost',
        name='localhost',
    )

    print("Creating flatpages fixtures")
    p, created = flatpages_app.FlatPage.objects.get_or_create(
        url='/about/',
        defaults=dict(
            registration_required=0,
            title='About',
            template_name='',
            content='About this site',
            enable_comments=0,
        )
    )
    p.sites.add(
        sites_app.Site.objects.get(domain='localhost', name='localhost'))


def create_user_fixtures(*args, **kwargs):
    print("Creating auth fixtures")
    auth_app.User.objects.get_or_create(
        username='admin',
        defaults=dict(
            first_name='Admin',
            last_name='Admin',
            is_active=1,
            is_superuser=1,
            is_staff=1,
            password="sha1$bc241$8bc918c29c4d1e313ca858bb1218b6c268b53961",
            email='admin@example.com',
        )
    )


signals.post_migrate.connect(
    create_site_flatpage_fixtures,
    sender=flatpages_app
)
signals.post_migrate.connect(create_user_fixtures, sender=auth_app)
