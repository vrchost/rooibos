import setuptools
from rooibos.version import getVersion


REQUIRES = """
attrs>=17.4.0
b2sdk==0.1.6
beautifulsoup4
bleach==3.1.4
bleach-whitelist==0.0.10
boto
Celery==4.2.1
configobj>=4.7.2,<=5.0.0
cryptography
django-appconf==1.0.3
django-cas-ng==3.5.10
django-compressor==2.2
django-extensions==2.0.7
django-pagination==1.0.7
django-ranged-fileresponse==0.1.2
django-storages==1.6.6
django-tagging==0.4.6
django-contrib-comments==1.8.0
Django==1.11.28
django-celery-results==1.0.4
flake8
flake8-docstrings
flake8-todo
flickrapi>=2
flup
gunicorn
ipaddr
markdown==3.1.1
pymysql
pep8
pep8-naming
pika
pillow
pycryptodome
PyPDF2
python-ldap
python-memcached
python-pptx
reportlab
requests
sqlparse
werkzeug
wfastcgi
wheel
requests
unicodecsv==0.14.1
django-shibboleth@https://github.com/knabar/django-shibboleth/archive/master.zip
"""


setuptools.setup(
    name='mdid',
    version=getVersion(),
    url='https://mdid.org',
    author='vrcHost LLC',
    author_email='info@vrchost.com',
    description='MDID is a digital media management system',
    long_description='MDID is a digital media management system with '
        'sophisticated tools for discovering, aggregating, and presenting '
        'digital media in a wide variety of learning spaces.',
    platforms=['Linux', 'Windows'],
    license='GPL',
    packages=['rooibos'],
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    python_requires='>=3.6',
)
