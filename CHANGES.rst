.. _change-log:

Change Log
----------

3.0.0 (2025-02-22)
~~~~~~~~~~~~~~~~~~

- Drop support for Python 3.7 and 3.8.

- Add support for Python 3.9 - 3.13.

- Rename private `zodburi._resolve_uri` helper to 
  `_get_uri_factory_and_dbkw` for clarity.  Preserve original name
  as a backward-compatibility alias (even though private, downstreams may
  have found it needful to use the function).

- Update unit tests using `pytest` idioms, dropping the
  `unittest.TestCase` classes.

- Remove Python2 compatibility shims.

- Replace use of deprecated `pkg_resources` APIs with new
  `importlib.metadata` versions.

- Deprecate ``?demostorage`` query string parameter in favour of
  ``demo:`` URI scheme.


2.6.0 (2023-05-17)
~~~~~~~~~~~~~~~~~~

- Drop support for ZODB4.

- Drop support for python < 3.7.


2.5.0 (2021-05-12)
~~~~~~~~~~~~~~~~~~

- Support both ZODB4 and ZODB5.

- Add support for PyPy.

- Add support for Python 3.8.

- Drop support for Python 3.4.

- Add support for ``demo:`` URI scheme.

2.4.0 (2019-01-11)
~~~~~~~~~~~~~~~~~~

- Add support for Python 3.7.

- Fix PendingDeprecationWarning about ``cgi.parse_qsl``. (PR #21)

2.3.0 (2017-10-17)
~~~~~~~~~~~~~~~~~~

- Fix parsing of ``zeo://`` URI with IPv6 address.

- Drop support for Python 3.3.

- Add support for Python 3.6.

2.2.2 (2017-05-05)
~~~~~~~~~~~~~~~~~~

- Fix transposed ``install_requires`` and ``tests_require`` lists in
  ``setup.py``.

2.2.1 (2017-04-18)
~~~~~~~~~~~~~~~~~~

- Fix breakage added in 2.2 to the ``zconfig`` resolver.

2.2 (2017-04-17)
~~~~~~~~~~~~~~~~

- Add support for additional database configuration parameters:
  ``pool_timeout``, ``cache_size_bytes``, ``historical_pool_size``,
  ``historical_cache_size``, ``historical_cache_size_bytes``,
  ``historical_timeout``, and ``large_record_size``.

2.1 (2017-04-17)
~~~~~~~~~~~~~~~~

- Add support for Python 3.4 and 3.5.

- Drop support for Python 2.6 and 3.2.

- Add missing ClientStorage constructor kw args to resolver.

2.0 (2014-01-05)
~~~~~~~~~~~~~~~~

- Update ``ZODB3`` meta-package dependency to ``ZODB`` + ``ZConfig`` + ``ZEO``.
  Those releases are what we import, and have final Py3k-compatible releases.

- Packaging:  fix missing ``url`` argument to ``setup()``.

2.0b1 (2013-05-02)
~~~~~~~~~~~~~~~~~~

- Add support for Python 3.2 / 3.3.

- Add ``setup.py docs`` alias (runs ``setup.py develop`` and installs
  documentation dependencies).

- Add ``setup.py dev`` alias (runs ``setup.py develop`` and installs
  testing dependencies).

- Automate building the Sphinx docs via ``tox``.

- Fix ``zconfig:`` URIs under Python 2.7.  The code worked around a bug in
  the stdlib's ``urlparse.urlsplit`` for Python < 2.7; that workaround broke
  under 2.7.  See https://github.com/Pylons/zodburi/issues/5

- Drop support for Python 2.5.

1.1 (2012-09-12)
~~~~~~~~~~~~~~~~

- Remove support for ``postgres://`` URIs, which will now be provided by
  the ``relstorage`` package.  Thanks to Georges Dubus for the patch!

1.0 (2012-06-07)
~~~~~~~~~~~~~~~~

- Add support for ``postgres://`` URIs.  Thanks to Georges Dubus for
  the patch!

- Pin dependencies to Python 2.5-compatible versions when testing with
  tox under Python 2.5.

- Update the documentation for publication to `ReadTheDocs
  <https://docs.pylonsproject.org/projects/zodburi/en/latest/>`_

1.0b1 (2011-08-21)
~~~~~~~~~~~~~~~~~~

- Initial release.
