import pytest
from flexmock import flexmock

from docker_build import _exec, _vagrant_driver


_up_output = """\
Bringing machine 'default' up with 'docker' provider...
==> default: Creating the container...
    default:   Name: test_build0_default_1426801518
    default:  Image: smerrill/vagrant-ubuntu
    default: Volume: /tmp/pytest-19/test_build0:/vagrant
    default:   Port: 2222:22
    default:
    default: Container created: fbf460de4e94806c
==> default: Starting container...
==> default: Provisioners will not be run since container doesn't support SSH.
"""

_up_output_failing = """\
A Vagrant environment or target machine is required to run this
command. Run `vagrant init` to create a new Vagrant environment. Or,
get an ID of a target machine from `vagrant global-status` to run
this command on. A final option is to change to a directory with a
Vagrantfile and to try again.
"""

_execution_error = _exec.ExecutionError('cmd', 'status', 'output')


def test_up():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args(
            'VAGRANT_DEFAULT_PROVIDER=docker vagrant',
            'up',
            chdir=None) \
        .and_return(_up_output) \
        .once()

    _vagrant_driver.up()


def test_up_chdir(tmpdir):
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args(
            'VAGRANT_DEFAULT_PROVIDER=docker vagrant',
            'up',
            chdir=tmpdir.strpath) \
        .and_return(_up_output) \
        .once()

    _vagrant_driver.up(tmpdir.strpath)


def test_up_execution_error():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args(
            'VAGRANT_DEFAULT_PROVIDER=docker vagrant',
            'up',
            chdir=None) \
        .and_raise(_execution_error) \
        .once()

    with pytest.raises(_vagrant_driver.VagrantError):
        _vagrant_driver.up()


def test_up_fail_no_match():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args(
            'VAGRANT_DEFAULT_PROVIDER=docker vagrant',
            'up',
            chdir=None) \
        .and_return(_up_output_failing) \
        .once()

    with pytest.raises(_vagrant_driver.VagrantError):
        _vagrant_driver.up()


def test_destroy():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args(
            'VAGRANT_DEFAULT_PROVIDER=docker vagrant',
            'destroy',
            '-f',
            chdir=None) \
        .once()

    _vagrant_driver.destroy()


def test_destroy_chdir(tmpdir):
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args(
            'VAGRANT_DEFAULT_PROVIDER=docker vagrant',
            'destroy',
            '-f',
            chdir=tmpdir.strpath) \
        .once()

    _vagrant_driver.destroy(chdir=tmpdir.strpath)


def test_destroy_fail():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args(
            'VAGRANT_DEFAULT_PROVIDER=docker vagrant',
            'destroy',
            '-f',
            chdir=None) \
        .and_raise(_execution_error) \
        .once()

    with pytest.raises(_vagrant_driver.VagrantError):
        _vagrant_driver.destroy()


def test_vagrant_context_manager():
    flexmock(_vagrant_driver).should_receive('up') \
        .with_args(chdir=None) \
        .ordered() \
        .once()
    flexmock(_vagrant_driver).should_receive('destroy') \
        .with_args(chdir=None) \
        .ordered() \
        .once()

    with _vagrant_driver.vagrant():
        pass


def test_vagrant_context_manager_chdir(tmpdir):
    flexmock(_vagrant_driver).should_receive('up') \
        .with_args(chdir=tmpdir.strpath) \
        .and_return('fbf460de4e94806c') \
        .ordered() \
        .once()
    flexmock(_vagrant_driver).should_receive('destroy') \
        .with_args(chdir=tmpdir.strpath) \
        .ordered() \
        .once()

    with _vagrant_driver.vagrant(tmpdir.strpath) as container_id:
        assert container_id == 'fbf460de4e94806c'
