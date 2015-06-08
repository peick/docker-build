from flexmock import flexmock
import pytest

from docker_build.image.api import RootFSLayer


def test_build():
    layer = RootFSLayer('rootfs.tar')
    layer._driver = flexmock(import_=lambda path: 'abcdef')

    layer.build()

    assert layer._image_id == 'abcdef'


def test_build_pre_post():
    result = []
    def pre():
        result.append(0)
    def post():
        result.append(1)

    layer = RootFSLayer('rootfs.tar', pre=pre, post=post)
    layer._driver = flexmock(import_=lambda path: 'abcdef')

    assert result == []
    layer.build()

    assert layer._image_id == 'abcdef'
    assert result == [0, 1]


def test_post_on_failure():
    result = []
    def post():
        result.append(1)

    layer = RootFSLayer('rootfs.tar', post=post)
    layer._driver = flexmock(import_=lambda path: 'abcdef')
    layer._driver.should_receive('import_').and_raise(Exception())

    assert result == []
    with pytest.raises(Exception):
        layer.build()

    assert layer._image_id is None
    assert result == [1]
