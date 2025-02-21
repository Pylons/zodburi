import contextlib
from importlib.metadata import distribution
import os
import pathlib
import tempfile
from unittest import mock
from urllib.parse import quote
import unittest
import warnings

import pytest
from ZEO.ClientStorage import ClientStorage
from ZODB.blob import BlobStorage
from ZODB.DemoStorage import DemoStorage
from ZODB.FileStorage import FileStorage
from ZODB.MappingStorage import MappingStorage


FS_FILENAME = "db.db"
FS_BLOBDIR = "blob"


@pytest.fixture(scope="function")
def tmpdir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.fixture(scope="function")
def zconfig_tmpfile():
    with tempfile.NamedTemporaryFile() as tmp:
        yield tmp


@pytest.fixture(scope="function")
def zconfig_path(zconfig_tmpfile):
    yield pathlib.Path(zconfig_tmpfile.name)


def _fs_resolver():
    from zodburi.resolvers import FileStorageURIResolver
    return FileStorageURIResolver()


def _mapping_resolver():
    from zodburi.resolvers import MappingStorageURIResolver
    return MappingStorageURIResolver()


def _client_resolver():
    from zodburi.resolvers import ClientStorageURIResolver
    return ClientStorageURIResolver()


def _zconfig_resolver():
    from zodburi.resolvers import ZConfigURIResolver
    return ZConfigURIResolver()

def _demo_resolver():
    from zodburi.resolvers import DemoStorageURIResolver
    return DemoStorageURIResolver()


@pytest.mark.parametrize("factory", [_fs_resolver, _mapping_resolver])
def test_interpret_kwargs_noargs(factory):
    resolver = factory()

    new, unused = resolver.interpret_kwargs({})

    assert new == {}
    assert unused == {}


@pytest.mark.parametrize("factory", [_fs_resolver, _mapping_resolver])
def test_interpret_kwargs_bytesize_args(factory):
    resolver = factory()
    names = sorted(resolver._bytesize_args)
    kwargs = {
        name: "10MB" for name in names
    }

    new, unused = resolver.interpret_kwargs(kwargs)

    assert sorted(new) == names

    if new:
        assert set(new.values()) == {10 * 1024 * 1024}


@pytest.mark.parametrize("factory", [_fs_resolver, _mapping_resolver])
def test_interpret_kwargs_int_args(factory):
    resolver = factory()
    names = sorted(resolver._int_args)
    kwargs = {
        name: "10" for name in names
    }

    new, unused = resolver.interpret_kwargs(kwargs)

    assert sorted(new) == sorted(new)

    if new:
        assert set(new.values()) == {10}


@pytest.mark.parametrize("factory", [_fs_resolver, _mapping_resolver])
def test_interpret_kwargs_string_args(factory):
    resolver = factory()
    names = sorted(resolver._string_args)
    kwargs = {
        name: "string" for name in names
    }

    new, unused = resolver.interpret_kwargs(kwargs)

    assert sorted(new) == names

    if new:
        assert set(new.values()) == {"string"}


@pytest.mark.parametrize("factory", [_fs_resolver, _mapping_resolver])
def test_interpret_kwargs_float_args(factory):
    resolver = factory()
    resolver._float_args = ("pi", "PI")
    names = sorted(resolver._float_args)
    kwargs = {
        "pi": "3.14",
        "PI": "3.14",
    }

    new, unussed = resolver.interpret_kwargs(kwargs)

    assert sorted(new) == names

    if new:
        assert set(new.values()) == {3.14}


@pytest.mark.parametrize("factory", [_fs_resolver, _mapping_resolver])
def test_interpret_kwargs_tuple_args(factory):
    resolver = factory()
    resolver._tuple_args = ("foo", "bar")
    names = sorted(resolver._tuple_args)
    kwargs = {
        name: "first,second,third" for name in names
    }

    new, unused = resolver.interpret_kwargs(kwargs)

    assert sorted(new) == names

    if new:
        assert set(new.values()) == {("first", "second", "third")}


@pytest.mark.parametrize("passed, expected", [
    ("1", 1),
    ("0", 0),
    ("true", 1),
    ("false", 0),
    ("on", 1),
    ("off", 0),
    ("yes", 1),
    ("no", 0),
])
@pytest.mark.parametrize("factory", [
    _fs_resolver,
    _client_resolver,
])
def test_fsresolver_interpres_kwargs_bool_args(factory, passed, expected):
    resolver = factory()
    kwargs = {"read_only": passed}

    new, unused = resolver.interpret_kwargs(kwargs)

    assert new == {"read_only": expected}


@pytest.mark.parametrize("uri, expected_args, expected_kwargs", [
    ("file:///tmp/foo/bar", ("/tmp/foo/bar",), {}),
    (
        "file:///tmp/foo/bar?read_only=true",
        ("/tmp/foo/bar",),
        {"read_only": 1}
    ),
    (
        "file://C:\\foo\\bar?read_only=true",
        ("C:\\foo\\bar",),
        {"read_only": 1}
    ),
    (
        "file:///tmp/../foo/bar?read_only=true",
        ("/foo/bar",),
        {"read_only": 1}
    ),
])
def test_fsresolver___call___mock_invoke_factory(
    uri, expected_args, expected_kwargs,
):
    resolver = _fs_resolver()

    factory, dbkw = resolver(uri)
    assert dbkw == {}

    with mock.patch("zodburi.resolvers.FileStorage") as fs_klass:
        factory()

    fs_klass.assert_called_once_with(*expected_args, **expected_kwargs)


def test_fsresolver___call___check_dbkw():
    resolver = _fs_resolver()
    factory, dbkw = resolver(
        "file:///tmp/foo/bar"
        "?connection_pool_size=1"
        "&connection_cache_size=1"
        "&database_name=dbname"
    )

    assert dbkw == {
        "connection_cache_size": "1",
        "connection_pool_size": "1",
        "database_name": "dbname",
    }


def test_fsresolver_invoke_factory(tmpdir):
    fs_dir = pathlib.Path(tmpdir)
    db_path = fs_dir / FS_FILENAME
    resolver = _fs_resolver()

    factory, dbkw = resolver(f"file://{tmpdir}/{FS_FILENAME}?quota=200")

    assert dbkw == {}

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, FileStorage)
        assert storage._quota == 200
        assert db_path.exists()


def test_fsresolver_invoke_factory_w_demostorage(tmpdir):
    fs_dir = pathlib.Path(tmpdir)
    db_path = fs_dir / FS_FILENAME
    resolver = _fs_resolver()

    with warnings.catch_warnings(record=True) as log:
        factory, dbkw = resolver(
            f"file://{tmpdir}/{FS_FILENAME}?demostorage=true",
        )

    assert dbkw == {}

    warned, = log
    assert issubclass(warned.category, DeprecationWarning)
    assert (
        "demostorage option is deprecated, use demo:// instead"
        in str(warned.message)
    )

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, DemoStorage)
        assert isinstance(storage.base, FileStorage)
        assert db_path.exists()


def test_fsresolver_invoke_factory_w_blobstorage(tmpdir):
    fs_dir = pathlib.Path(tmpdir)
    db_path = fs_dir / FS_FILENAME
    blob_dir = fs_dir / FS_BLOBDIR
    quoted = quote(str(blob_dir))
    resolver = _fs_resolver()

    factory, dbkw = resolver(
        f"file://{tmpdir}/{FS_FILENAME}?quota=200"
        f"&blobstorage_dir={quoted}&blobstorage_layout=bushy"
    )

    assert dbkw == {}

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, BlobStorage)
        assert blob_dir.exists()
        assert db_path.exists()


def test_fsresolver_invoke_factory_w_blobstorage_and_demostorage(tmpdir):
    fs_dir = pathlib.Path(tmpdir)
    db_path = fs_dir / FS_FILENAME
    blob_dir = fs_dir / FS_BLOBDIR
    quoted = quote(str(blob_dir))
    resolver = _fs_resolver()

    with warnings.catch_warnings(record=True) as log:
        factory, dbkw = resolver(
            f"file://{tmpdir}/{FS_FILENAME}?quota=200&demostorage=true"
            f"&blobstorage_dir={quoted}&blobstorage_layout=bushy"
        )

    assert dbkw == {}

    warned, = log
    assert issubclass(warned.category, DeprecationWarning)
    assert (
        "demostorage option is deprecated, use demo:// instead"
        in str(warned.message)
    )

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, DemoStorage)
        assert isinstance(storage.base, BlobStorage)
        assert blob_dir.exists()
        assert db_path.exists()


@pytest.mark.parametrize("uri, expected_args, expected_kwargs", [
    ("zeo://localhost", (("localhost", 9991),), {}),
    ("zeo://localhost:8080?debug=true", (("localhost", 8080),), {"debug": 1}),
    ("zeo://:1234?debug=true", (("", 1234),), {"debug": 1}),
    ("zeo://[::1]", (("::1", 9991),), {}),
    ("zeo://[::1]:9990?debug=true", (("::1", 9990),), {"debug": 1}),
    ("zeo:///var/sock?debug=true", ("/var/sock",), {"debug": 1}),
    ("zeo:///var/nosuchfile?wait=false", ("/var/nosuchfile",), {"wait": 0}),
    (
        (
            'zeo:///var/nosuchfile?'
            'storage=main&'
            'cache_size=1kb&'
            'name=foo&'
            'client=bar&'
            'var=baz&'
            'min_disconnect_poll=2&'
            'max_disconnect_poll=3&'
            'wait_for_server_on_startup=true&'
            'wait=4&'
            'wait_timeout=5&'
            'read_only=6&'
            'read_only_fallback=7&'
            'drop_cache_rather_verify=true&'
            'username=monty&'
            'password=python&'
            'realm=blat&'
            'blob_dir=some/dir&'
            'shared_blob_dir=true&'
            'blob_cache_size=1kb&'
            'blob_cache_size_check=8&'
            'client_label=fink&'
        ),
        ('/var/nosuchfile',),
        dict(
            storage='main',
            cache_size=1024,
            name='foo',
            client='bar',
            var='baz',
            min_disconnect_poll=2,
            max_disconnect_poll=3,
            wait_for_server_on_startup=1,
            wait=4,
            wait_timeout=5,
            read_only=6,
            read_only_fallback=7,
            drop_cache_rather_verify=1,
            username='monty',
            password='python',
            realm='blat',
            blob_dir='some/dir',
            shared_blob_dir=1,
            blob_cache_size=1024,
            blob_cache_size_check=8,
            client_label='fink',
        ),
    ),
])
def test_client_resolver___call___(uri, expected_args, expected_kwargs):
    resolver = _client_resolver()

    factory, dbkw = resolver(uri)

    assert dbkw == {}

    with mock.patch("zodburi.resolvers.ClientStorage") as cs:
        factory()

    cs.assert_called_once_with(*expected_args, **expected_kwargs)

def test_client_resolver___call___check_dbkw():
    resolver = _client_resolver()

    factory, dbkw = resolver(
        "zeo://localhost:8080?"
        "connection_pool_size=1&"
        "connection_cache_size=1&"
        "database_name=dbname"
    )
    assert dbkw == {
        "connection_pool_size": "1",
        "connection_cache_size": "1",
        "database_name": "dbname",
    }


def test_client_resolver_invoke_factory():
    resolver = _client_resolver()

    factory, dbkw = resolver("zeo:///var/nosouchfile?wait=false")
    assert dbkw == {}

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, ClientStorage)
        # Stub out the storage's server to allow close to complete.
        storage._server = mock.Mock(spec_set=("close",))


def test_client_resolver_invoke_factory_w_demostorage():
    resolver = _client_resolver()

    with warnings.catch_warnings(record=True) as log:
        factory, dbkw = resolver(
            f"zeo:///var/nosuchfile?demostorage=true&wait=false",
        )

    assert dbkw == {}

    warned, = log
    assert issubclass(warned.category, DeprecationWarning)
    assert (
        "demostorage option is deprecated, use demo:// instead"
        in str(warned.message)
    )

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, DemoStorage)
        assert isinstance(storage.base, ClientStorage)
        # Stub out the storage's server to allow close to complete.
        storage.base._server = mock.Mock(spec_set=("close",))


def test_zconfig_resolver___call___check_dbkw(zconfig_path):
    zconfig_path.write_text(
        """\
<mappingstorage>
</mappingstorage>
"""
    )
    resolver = _zconfig_resolver()
    factory, dbkw = resolver(f"zconfig://{zconfig_path}?foo=bar")

    assert dbkw == {"foo": "bar"}


def test_zconfig_resolver___call___w_unknown_storage(zconfig_path):
    zconfig_path.write_text(
        """\
<mappingstorage x>
</mappingstorage>
"""
    )
    resolver = _zconfig_resolver()
    with pytest.raises(KeyError):
        resolver(f"zconfig://{zconfig_path}#y")



def test_zconfig_resolver_invoke_factory_w_named_storage(zconfig_path):
    zconfig_path.write_text(
        """\
<demostorage foo>
</demostorage>

<mappingstorage bar>
</mappingstorage>
"""
    )
    resolver = _zconfig_resolver()
    factory, dbkw = resolver(f"zconfig://{zconfig_path}#bar")

    assert dbkw == {}

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)


def test_zconfig_resolver_invoke_factory_w_anonymous_storage(zconfig_path):
    zconfig_path.write_text(
        """\
<mappingstorage>
</mappingstorage>

<demostorage demo>
</demostorage>
"""
    )
    resolver = _zconfig_resolver()
    factory, dbkw = resolver(f"zconfig://{zconfig_path}")

    assert dbkw == {}

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)


def test_zconfig_resolver_invoke_factory_w_anon_db_w_defaults(zconfig_path):
    zconfig_path.write_text(
        """\
<zodb>
 <mappingstorage>
 </mappingstorage>
</zodb>
"""
    )
    resolver = _zconfig_resolver()
    factory, dbkw = resolver(f"zconfig://{zconfig_path}")

    assert dbkw == {
        "connection_cache_size": 5000,
        "connection_cache_size_bytes": 0,
        "connection_historical_cache_size": 1000,
        "connection_historical_cache_size_bytes": 0,
        "connection_historical_pool_size": 3,
        "connection_historical_timeout": 300,
        "connection_large_record_size": 16777216,
        "connection_pool_size": 7,
    }

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)


def test_zconfig_resolver_invoke_factory_w_named_db_w_explicit(zconfig_path):
    zconfig_path.write_text(
        """\
<zodb x>
 <mappingstorage>
 </mappingstorage>

 database-name foo
 cache-size 20000
 pool-size 5
</zodb>
"""
    )
    resolver = _zconfig_resolver()
    factory, dbkw = resolver(f"zconfig://{zconfig_path}#x")

    assert dbkw == {
        "database_name": "foo",
        "connection_cache_size": 20000,
        "connection_cache_size_bytes": 0,
        "connection_historical_cache_size": 1000,
        "connection_historical_cache_size_bytes": 0,
        "connection_historical_pool_size": 3,
        "connection_historical_timeout": 300,
        "connection_large_record_size": 16777216,
        "connection_pool_size": 5,
    }

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)


def test_zconfig_resolver_invoke_factory_w_all_options(zconfig_path):
    from zodburi import CONNECTION_PARAMETERS, BYTES_PARAMETERS

    all_params = [
        (
            name.replace("_", "-"),
            "%sMB" % i if name in BYTES_PARAMETERS else str(i),
        )
        for (i, name) in enumerate(CONNECTION_PARAMETERS)
    ]
    params_str = "\n".join(
        [f"{name} {value}" for name, value in all_params]
    )
    zconfig_path.write_text(
        f"""\
<zodb x>
<mappingstorage>
</mappingstorage>
database-name foo
{params_str}
</zodb>
"""
    )
    resolver = _zconfig_resolver()
    factory, dbkw = resolver(f"zconfig://{zconfig_path}#x")

    expected = {"database_name": "foo"}

    for i, parameter in enumerate(CONNECTION_PARAMETERS):
        cparameter = f"connection_{parameter}"

        if parameter in BYTES_PARAMETERS:
            expected[cparameter] = i * 1024 * 1024
        else:
            expected[cparameter] = i

    assert dbkw == expected

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)



def test_resolve_uri_w_zconfig(zconfig_path):
    from zodburi import resolve_uri

    zconfig_path.write_text("""\
<zodb>
 <mappingstorage>
 </mappingstorage>
</zodb>
"""
    )
    factory, dbkw = resolve_uri(f"zconfig://{zconfig_path}")

    assert dbkw == {
        "cache_size": 5000,
        "cache_size_bytes": 0,
        "historical_cache_size": 1000,
        "historical_cache_size_bytes": 0,
        "historical_pool_size": 3,
        "historical_timeout": 300,
        "large_record_size": 16777216,
        "pool_size": 7,
        "database_name": "unnamed",
    }

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)


def test_mapping_resolver_wo_qs():
    resolver = _mapping_resolver()

    factory, dbkw = resolver("memory://")

    assert dbkw == {}

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)
        assert storage.__name__ == ""


def test_mapping_resolver_w_qs():
    resolver = _mapping_resolver()

    factory, dbkw = resolver(
        "memory://storagename?connection_cache_size=100&database_name=fleeb"
    )

    assert dbkw == {
        "connection_cache_size": "100",
        "database_name": "fleeb"
    }

    with contextlib.closing(factory()) as storage:
        assert isinstance(storage, MappingStorage)
        assert storage.__name__ == "storagename"


def test_demo_resolver_w_invalid_uri_no_match():
    from zodburi.resolvers import InvalidDemoStorgeURI

    resolver = _demo_resolver()

    with pytest.raises(InvalidDemoStorgeURI):
        resolver("bogus:name")


def test_demo_resolver_w_invalid_uri_kwargs_in_base():
    from zodburi.resolvers import InvalidDemoStorgeURI

    resolver = _demo_resolver()

    with pytest.raises(InvalidDemoStorgeURI):
        resolver(
            "demo:"
            "(file:///tmp/blah?pool_size=1234)/"
            "(file:///tmp/qux)"
        )


def test_demo_resolver_w_invalid_uri_kwargs_in_changes():
    from zodburi.resolvers import InvalidDemoStorgeURI

    resolver = _demo_resolver()

    with pytest.raises(InvalidDemoStorgeURI):
        resolver(
            "demo:"
            "(file:///tmp/blah)/"
            "(file:///tmp/qux?pool_size=1234)"
        )


def test_demo_resolver_invoke_factory_w_fs_overlay(tmpdir):
    fs_dir = pathlib.Path(tmpdir)
    base_path = fs_dir / "base.fs"
    changes_path = fs_dir / "changes.fs"
    assert not base_path.exists()
    assert not changes_path.exists()
    demo_uri = (
        f"demo:"
        f"(file://{base_path})/"
        f"(file://{changes_path}"
        f"?quota=200)"
    )

    resolver = _demo_resolver()

    factory, dbkw = resolver(demo_uri)

    assert dbkw == {}

    with contextlib.closing(factory()) as demo:
        assert isinstance(demo, DemoStorage)
        assert isinstance(demo.base, FileStorage)
        assert isinstance(demo.changes, FileStorage)
        assert base_path.exists()
        assert changes_path.exists()
        assert demo.changes._quota == 200


def test_demo_resolver_invoke_factory_w_qs_parms(tmpdir):
    fs_dir = pathlib.Path(tmpdir)
    base_path = fs_dir / "base.fs"
    changes_path = fs_dir / "changes.fs"
    assert not base_path.exists()
    assert not changes_path.exists()
    demo_uri = "demo:(memory://111)/(memory://222)#foo=bar&abc=def"

    resolver = _demo_resolver()

    factory, dbkw = resolver(demo_uri)

    assert dbkw == {'foo': 'bar', 'abc': 'def'}

    with contextlib.closing(factory()) as demo:
        assert isinstance(demo, DemoStorage)
        assert isinstance(demo.base, MappingStorage)
        demo.base.__name__ == '111'
        assert isinstance(demo.changes, MappingStorage)
        assert demo.changes.__name__ == '222'


def test_entry_points():
    from zodburi import resolvers

    our_eps = {
        ep.name: ep for ep in distribution("zodburi").entry_points
    }
    expected = [
        ('memory', resolvers.MappingStorageURIResolver),
        ('zeo', resolvers.ClientStorageURIResolver),
        ('file', resolvers.FileStorageURIResolver),
        ('zconfig', resolvers.ZConfigURIResolver),
        ('demo', resolvers.DemoStorageURIResolver),
    ]
    for name, cls in expected:
        target = our_eps[name].load()
        assert isinstance(target, cls)
