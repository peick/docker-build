import contextlib
from flexmock import flexmock
import pytest

from docker_build import _docker_driver, _vagrant_driver
from docker_build._image import VagrantLayer


@contextlib.contextmanager
def _mock_contextmanager(value):
    yield value


@pytest.mark.parametrize('vagrant_filename, vagrant_dir_or_file', [
    ('Vagrantfile',     ''),
    ('Vagrantfile',     '../'),
    ('custom-file.vgt', ''),
])
def test_build(tmpdir, datadir, vagrant_filename, vagrant_dir_or_file):
    content = datadir.join('vagrant.py.Vagrantfile').read()

    vagrant_file = tmpdir.join(vagrant_filename)
    vagrant_file.write(content)

    file_or_dir = vagrant_file.join(vagrant_dir_or_file).strpath

    flexmock(_vagrant_driver).should_receive('vagrant') \
        .with_args(tmpdir.strpath) \
        .and_return(_mock_contextmanager('fbf460de4e94806c')) \
        .once()

    flexmock(_docker_driver).should_receive('commit') \
        .with_args('fbf460de4e94806c', str) \
        .and_return('15878aca572de99b4381c949') \
        .once()

    layer = VagrantLayer(file_or_dir)
    layer.build()

    assert layer._image_id == '15878aca572de99b4381c949'

