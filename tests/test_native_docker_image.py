from flexmock import flexmock

from docker_build import _docker_driver
from docker_build._image import NativeDockerImageLayer


def test_build():
    image = NativeDockerImageLayer('test/sample')

    image._driver = flexmock()
    image._driver.should_receive('inspect_id') \
        .and_return(None) \
        .and_return('abcd')
    image._driver.should_receive('pull').once()
    image._driver.should_receive('tag').with_args('abcd', 'test/sample')

    image.build()

    assert image._image_id == 'abcd'


def test_build_existing():
    image = NativeDockerImageLayer('test/sample')

    image._driver = flexmock()
    image._driver.should_receive('inspect_id').and_return('abcd').once()

    image.build()

    assert image._image_id == 'abcd'


def test_build_with_base():
    base  = flexmock(NativeDockerImageLayer('test/example'),
        _already_built=True,
        _image_id='abcd')
    image = NativeDockerImageLayer('test/sample', base=base)

    base._driver = flexmock()
    image._driver = flexmock()

    image._driver.should_receive('tag').with_args('abcd', 'test/sample').once()

    image.build()
    assert image._image_id == base._image_id == 'abcd'
