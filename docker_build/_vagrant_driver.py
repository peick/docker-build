import contextlib
import re

from . import _exec
from ._exec import wrap_execution_error, ExecutionError


class VagrantError(Exception):
    pass


def _exec_vagrant_cmd(command, *args, **kwargs):
    return _exec.exec_cmd(
        'VAGRANT_DEFAULT_PROVIDER=docker vagrant', command, *args, **kwargs)


@wrap_execution_error(VagrantError)
def up(chdir=None):
    """Calls `vagrant up` and returns the docker container id on success.
    """
    output = _exec_vagrant_cmd('up', chdir=chdir)
    match = re.search(r'Container created: (\S+)\s*', output)
    if not match:
        raise VagrantError('Container id not found.')

    container_id = match.group(1)
    return container_id


@wrap_execution_error(VagrantError)
def destroy(chdir=None):
    try:
        _exec_vagrant_cmd('destroy', '-f', chdir=chdir)
    except ExecutionError as error:
        raise VagrantError(error)


@contextlib.contextmanager
def vagrant(chdir=None):
    container_id = up(chdir=chdir)
    yield container_id
    destroy(chdir=chdir)

