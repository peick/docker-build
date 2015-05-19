import os
import pytest
from flexmock import flexmock

from docker_build._image import (
    RootFSLayer,
    VagrantLayer,
    )


def test_vagrant_layer_missing_argument():
    with pytest.raises(TypeError):
        VagrantLayer()


def test_rootfs_layer_missing_argument():
    with pytest.raises(TypeError):
        RootFSLayer()


def test_image_dependencies(tmpdir):
    a_dir = tmpdir.join('A').strpath
    b_dir = tmpdir.join('B').strpath
    c_dir = tmpdir.join('C').strpath

    flexmock(os.path).should_receive('exists').with_args(a_dir).and_return(True)
    flexmock(os.path).should_receive('exists').with_args(b_dir).and_return(True)
    flexmock(os.path).should_receive('exists').with_args(c_dir).and_return(True)

    base = VagrantLayer(a_dir)
    dep1 = VagrantLayer(b_dir, base=base)
    dep2 = VagrantLayer(c_dir, base=dep1)

    flexmock(base).should_receive('_build').once()
    flexmock(dep1).should_receive('_build').once()
    flexmock(dep2).should_receive('_build').once()

    dep2.build()

    # only build once
    dep2.build()

