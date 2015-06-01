import logging
import os
import pipes
import subprocess


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
            except ExecutionError as error:
                raise exc_type(error)

        #_wrap.func_name = func.func_name
        return _wrap

    return _deco


def exec_cmd(binary, *command_args, **kwargs):
    chdir = kwargs.get('chdir', None)
    can_fail = kwargs.get('can_fail', False)
    stdin = kwargs.get('stdin', None)

    args = [pipes.quote(arg) for arg in command_args]
    cmd  = '%s %s' % (binary, ' '.join(args))
    if stdin:
        cmd = '%s < %s' % (cmd, stdin)
    if chdir:
        cmd = 'cd %s && %s' % (chdir, cmd)
    cmd += ' 2>&1'
    _log.debug(cmd)

    try:
        output = subprocess.check_output(cmd, shell=True)
        returncode = 0
    except subprocess.CalledProcessError as error:
        output = ''
        returncode = error.returncode
        if not can_fail:
            raise ExecutionError(cmd, returncode, output)

    if can_fail:
        return returncode, output

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

