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

requires = ['ZODB3']
tests_require = requires + ['mock']

setup(name='zodburi',
      version='1.2dev',
      description=('Constructs ZODB storage instances from URIs.'),
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "License :: Repoze Public License",
        ],
      keywords='zodb zodbconn',
      author="Chris Rossi",
      author_email="pylons-discuss@googlegroups.com",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = requires,
      install_requires = tests_require,
      test_suite="zodburi",
      entry_points="""\
      [zodburi.resolvers]
      zeo = zodburi.resolvers:client_storage_resolver
      file = zodburi.resolvers:file_storage_resolver
      zconfig = zodburi.resolvers:zconfig_resolver
      memory = zodburi.resolvers:mapping_storage_resolver
      """,
      )
