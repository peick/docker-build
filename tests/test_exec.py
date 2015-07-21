import pytest
from six import BytesIO
from docker_build._exec import exec_cmd, ExecutionError


def _expect_output():
    return open('/bin/cat', 'rb').read()


def test_exec_cmd():
    output = exec_cmd('/bin/cat', '/bin/cat')
    assert output == _expect_output()


#def test_exec_cmd_chdir():
#    output = exec_cmd('/bin/cat', 'bin/cat', chdir='/')
#    assert output == _expect_output()


def test_exec_cmd_fail():
    with pytest.raises(ExecutionError):
        exec_cmd('/')


def test_exec_cmd_stdin():
    output = exec_cmd('/bin/cat', stdin=b'test123')
    assert output == b'test123'

    output = exec_cmd('/bin/cat', stdin=BytesIO(b'test123'))
    assert output == b'test123'


def test_exec_cmd_can_fail():
    status, stdout, stderr = exec_cmd('/', can_fail=True)
    assert status
    assert stdout == None
    assert stderr

