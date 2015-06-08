from flexmock import flexmock
import pytest

from docker_build import _docker_driver
from docker_build.image.api import DockerfileImageLayer, DockerfileDirectImageLayer


@pytest.mark.parametrize('docker_filename, docker_dir_or_file', [
    ('Dockerfile',         ''),
    ('Dockerfile',         '../'),
    ('custom-file.docker', ''),
])
def test_build(tmpdir, datadir, docker_filename, docker_dir_or_file):
    content = datadir.join('dockerfile.py.Dockerfile').read()

    docker_file = tmpdir.join(docker_filename)
    docker_file.write(content)

    file_or_dir = docker_file.join(docker_dir_or_file).strpath

    flexmock(_docker_driver).should_receive('build') \
        .with_args(str, chdir=tmpdir.strpath) \
        .and_return('b7722e0317a4') \
        .once()

    layer = DockerfileImageLayer(file_or_dir)
    layer.build()

    assert layer._image_id == 'b7722e0317a4'


def test_build_direct():
    base = flexmock(
        build=lambda: None,
        _image_id='b7722e0317a4',
        add_child=lambda child: None)
    layer = DockerfileDirectImageLayer(base=base, cmd='pwd')

    fake_layer = flexmock(_image_id='abcdef')
    flexmock(DockerfileImageLayer) \
        .new_instances(fake_layer)
    fake_layer.should_receive('build') \
        .once()

    layer.build()
    assert layer._image_id == 'abcdef'

