import os.path
import sys
import tempfile
from textwrap import dedent

from flexmock import flexmock
import pytest

import docker_build.cli
from docker_build.image.api import BaseImageLayer


class Stdin(object):
    def __init__(self):
        self._original = sys.stdin

    def __enter__(self):
        sys.stdin = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdin = self._original

    def read(self):
        pass

    def readline(self):
        return self._original.readline()

    @property
    def encoding(self):
        return self._original.encoding


def _run_cli(tmpdir, args, stdin=None):
    with Stdin() as stdin_wrapper:
        if stdin:
            stdin_temp = tempfile.NamedTemporaryFile(dir=tmpdir.strpath, delete=False)
            stdin_temp.write(stdin.encode('utf-8'))
            stdin_temp.close()
            flexmock(stdin_wrapper).should_receive('read').and_return(stdin).once()
        else:
            flexmock(stdin_wrapper).should_receive('read').never()

        docker_build.cli.main(args)

# -----------------------------------------------------------------------------

@pytest.mark.parametrize('stdin', [
    dedent("""
        Image('dockerbuild_test/example')
    """),

    dedent("""
        load_config_file('tests/raw/rootfs.py')
    """),

    dedent("""
        load_config_file('tests/raw/include_sub_directory.py')
    """),
])
def test_stdin(tmpdir, stdin):
    _run_cli(tmpdir, ['--check-config', '-c', '-'], stdin)


@pytest.mark.parametrize('filename', [
    'tests/raw/import_python_stdlib.py',
    'tests/raw/include_sub_directory.py',
    'tests/raw/rootfs.py',
    'tests/raw/registry.py',
    'tests/raw/metadata.py',
])
def test_filename(tmpdir, filename):
    _run_cli(tmpdir, ['--check-config', '-c', filename])


@pytest.mark.parametrize('stdin', [
    '  bad_indent = True',
    'a =',
    'Image(',
])
def test_stdin_bad_config(tmpdir, stdin):
    with pytest.raises(SystemExit):
        _run_cli(tmpdir, ['--check-config', '-c', '-'], stdin)


@pytest.mark.parametrize('filename', [
    'tests/raw/registry.py',
])
def test_build(tmpdir, filename):
    flexmock(BaseImageLayer).should_receive('build').once()
    flexmock(BaseImageLayer).should_receive('is_uploaded').and_return(False).once()
    flexmock(BaseImageLayer).should_receive('upload_to_registry').once()
    _run_cli(tmpdir, ['-c', filename])
