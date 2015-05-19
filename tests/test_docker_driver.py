from flexmock import flexmock
import pytest

from docker_build import _exec, _docker_driver


_built_out = """\
Sending build context to Docker daemon 2.048 kB
Sending build context to Docker daemon
Step 0 : FROM registry:0.9.1
 ---> 57d790e4cd1d
Step 1 : RUN echo
 ---> Running in 0a48745b2e2c

 ---> b7722e0317a4
Removing intermediate container 0a48745b2e2c
Successfully built b7722e0317a4
"""


def test_build():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'build', '--rm', '-t', 'test/sample', '.', chdir=None) \
        .and_return(_built_out) \
        .once()
    result = _docker_driver.build('test/sample')
    assert result == 'b7722e0317a4'

def test_commit():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'commit', '-p', 'abcd').once()
    _docker_driver.commit('abcd')

def test_commit_repotag():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'commit', '-p', 'abcd', 'test/sample').once()
    _docker_driver.commit('abcd', 'test/sample')

def test_inspect():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'inspect', 'abcd', can_fail=True) \
        .and_return(0, '[{"a": 4}]').once()
    result = _docker_driver.inspect('abcd')
    assert result == {"a": 4}

def test_inspect_format():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'inspect', '-f', '{{.Id}}', 'abcd', can_fail=True) \
        .and_return(0, 'abcdef').once()
    result = _docker_driver.inspect('abcd', '{{.Id}}')
    assert result == 'abcdef'

def test_inspect_missing_image():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'inspect', 'abcd', can_fail=True) \
        .and_return(1, '').once()
    result = _docker_driver.inspect('abcd')
    assert result is None

def test_login():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'login', '-u', 'my-user', '-p', 'my-pwd', '-e', ' ', 'localhost:5005').once()
    _docker_driver.login('localhost:5005', 'my-user', 'my-pwd')

def test_logout():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'logout', 'localhost:5005').once()
    _docker_driver.logout('localhost:5005')

def test_pull():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'pull', 'test/sample').once()
    _docker_driver.pull('test/sample')

def test_push():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'push', 'test/sample').once()
    _docker_driver.push('test/sample')

def test_rm_force():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'rm', 'abcd', '-f', can_fail=True) \
        .and_return(2, 'x').once()
    result = _docker_driver.rm('abcd')
    assert result == 2

def test_rm_no_force():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'rm', 'abcd').once()
    _docker_driver.rm('abcd', force=False)

def test_rmi_force():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'rmi', 'abcd', '-f', can_fail=True) \
        .and_return(2, 'x').once()
    result = _docker_driver.rmi('abcd')
    assert result == 2

def test_rmi_no_force():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'rmi', 'abcd').once()
    _docker_driver.rmi('abcd', force=False)

#def test_run():
#    flexmock(_exec).should_receive('exec_cmd') \
#        .with_args('docker', 'run', 'test/sample', 'ls').once()
#    _docker_driver.run('test/sample', 'ls')

def test_tag():
    flexmock(_exec).should_receive('exec_cmd') \
        .with_args('docker', 'tag', 'abcd', 'test/sample').once()
    _docker_driver.tag('abcd', 'test/sample')
