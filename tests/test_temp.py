import os
import pytest

from docker_build._temp import TempFileLink, TempDirectory


class _ExampleException(Exception):
    pass


def test_templinkfile(tmpdir):
    link = tmpdir.join('lnk').strpath
    temp = TempFileLink(tmpdir.strpath, link)

    assert not os.path.exists(link)
    with temp:
        assert os.path.exists(link)
        assert os.path.islink(link)
    assert not os.path.exists(link)


def test_templinkfile_error(tmpdir):
    link = tmpdir.join('lnk').strpath

    with pytest.raises(_ExampleException):
        with TempFileLink(tmpdir.strpath, link):
            assert os.path.exists(link)
            raise _ExampleException()

    assert not os.path.exists(link)


def test_tempdirectory():
    with TempDirectory() as path:
        assert os.path.exists(path)
        assert os.path.isdir(path)
    assert not os.path.exists(path)


def test_tempdirectory_error():
    with pytest.raises(_ExampleException):
        with TempDirectory() as path:
            assert os.path.exists(path)
            raise _ExampleException()

    assert not os.path.exists(path)
