import os

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()
except:
    README = ''

try:
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except:
    CHANGES = ''

requires = ['ZODB', 'ZConfig', 'ZEO']
tests_require = requires + ['mock']
testing_extras = tests_require + ['nose', 'coverage']
docs_extras = tests_require + [
    'Sphinx >= 1.3.1',
    'repoze.sphinx.autointerface',
    'pylons-sphinx-themes',
]

setup(name='zodburi',
      version='2.2.2',
      description=('Construct ZODB storage instances from URIs.'),
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "License :: Repoze Public License",
        ],
      keywords='zodb zodbconn',
      author="Chris Rossi",
      author_email="pylons-discuss@googlegroups.com",
      url="http://pylonsproject.org",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = tests_require,
      install_requires = requires,
      test_suite="zodburi",
      entry_points="""\
      [zodburi.resolvers]
      zeo = zodburi.resolvers:client_storage_resolver
      file = zodburi.resolvers:file_storage_resolver
      zconfig = zodburi.resolvers:zconfig_resolver
      memory = zodburi.resolvers:mapping_storage_resolver
      """,
      extras_require = {
        'testing': testing_extras,
        'docs': docs_extras,
      },
      )
