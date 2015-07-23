import logging
import os
import pipes
import subprocess
import threading


_log = logging.getLogger(__name__)


class ExecutionError(Exception):
    def __init__(self, cmd, status, stdout, stderr):
        self.command = cmd
        self.status = status
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        indented = ['  %s' % s for s in self.stderr.splitlines()]
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


def _readerthread(fh, logger, out):
    while True:
        data = fh.read()
        if not data:
            break
        if logger:
            logger(data)
        out.append(data)


def _communicate(popen, stdin=None):
    stdout = []
    stderr = []

    logger = lambda v: _log.debug('[stdout] %s', v)
    stdout_thread = threading.Thread(target=_readerthread,
                                     args=(popen.stdout, logger, stdout))
    logger = lambda v: _log.debug('[stderr] %s', v)
    stderr_thread = threading.Thread(target=_readerthread,
                                     args=(popen.stderr, logger, stderr))

    stdout_thread.setDaemon(True)
    stderr_thread.setDaemon(True)

    stdout_thread.start()
    stderr_thread.start()

    if stdin is not None:
        if hasattr(stdin, 'read'):
            stdin_data = stdin.read()
        else:
            stdin_data = stdin
        popen.stdin.write(stdin_data)
        popen.stdin.close()

    stdout_thread.join()
    stderr_thread.join()

    stdout = b''.join(stdout)
    stderr = b''.join(stderr)

    popen.wait()
    return (popen.returncode, stdout, stderr)


def exec_cmd(binary, *command_args, **kwargs):
    change_dir = kwargs.pop('chdir', None)
    can_fail = kwargs.pop('can_fail', False)
    stdin = kwargs.pop('stdin', None)
    assert not kwargs, kwargs

    stdin_pipe = subprocess.PIPE if stdin else None
    command = [binary] + list(command_args)
    _log.debug(' '.join(command))
    try:
        with chdir(change_dir):
            popen = subprocess.Popen(command,
                                     close_fds=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdin=stdin_pipe)
    except os.error as error:
        status = -1
        stdout = None
        stderr = str(error)
        if can_fail:
            return (status, stdout, stderr)
        raise ExecutionError(binary, status, stdout, stdout)

    status, stdout, stderr = _communicate(popen, stdin)

    if not can_fail and status:
        raise ExecutionError(binary, status, stdout, stderr)

    if can_fail:
        return status, stdout

    return stdout


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

