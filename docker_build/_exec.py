import commands
import logging
import os


_log = logging.getLogger(__name__)


class ExecutionError(Exception):
    def __init__(self, cmd, status, output):
        self.command = cmd
        self.status = status
        self.output = output

    def __str__(self):
        indented = ['  %s' % s for s in self.output.splitlines()]
        indented = '\n'.join(indented)
        return 'Execution failed for %s:\n%s' % (self.command, indented)


def wrap_execution_error(exc_type):
    """Decorator function that catches ExecutionError and transforms it into
    an exception of type `exc_type`.
    """
    def _deco(func):
        def _wrap(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ExecutionError, error:
                raise exc_type(error)

        _wrap.func_name = func.func_name
        return _wrap

    return _deco


def exec_cmd(binary, *command_args, **kwargs):
    chdir = kwargs.get('chdir', None)
    can_fail = kwargs.get('can_fail', False)
    stdin = kwargs.get('stdin', None)

    args = [commands.mkarg(arg) for arg in command_args]
    cmd  = '%s %s' % (binary, ' '.join(args))
    if stdin:
        cmd = '%s < %s' % (cmd, stdin)
    if chdir:
        cmd = 'cd %s && %s' % (chdir, cmd)
    _log.debug(cmd)
    status, output = commands.getstatusoutput(cmd)

    if status and not can_fail:
        raise ExecutionError(cmd, status, output)

    if can_fail:
        return status, output

    return output


class chdir(object):
    """Context manager to change the working directory.
    """
    def __init__(self, directory):
        self._directory = directory
        self._cwd = os.getcwd()

    def __enter__(self):
        if self._directory:
            os.chdir(self._directory)

    def __exit__(self, exc_type, exc_value, traceback):
        if self._directory:
            os.chdir(self._cwd)

