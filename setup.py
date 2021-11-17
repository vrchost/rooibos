import os.path
import re
import setuptools
from rooibos.version import get_version


requirements = os.path.join(os.path.dirname(__file__), 'requirements.txt')

with open(requirements) as r:
    REQUIRES = [
        package
        for package in r.readlines()
        if re.match(r'^[a-z]', package, re.IGNORECASE)
    ]


setuptools.setup(
    name='mdid',
    version=get_version(),
    url='https://mdid.org',
    author='vrcHost LLC',
    author_email='info@vrchost.com',
    description='MDID is a digital media management system',
    long_description='MDID is a digital media management system with '
        'sophisticated tools for discovering, aggregating, and presenting '
        'digital media in a wide variety of learning spaces.',
    platforms=['Linux', 'Windows'],
    license='GPL',
    packages=['rooibos', 'loris', 'django_shibboleth'],
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'mdid = rooibos.__main__:main',
        ],
    }
)
