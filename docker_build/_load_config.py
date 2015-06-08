import errno
import imp
import logging
import os
import sys
import traceback

from ._exec import chdir
from ._registry import Registry
from .image.api import BaseImageLayer


_log = logging.getLogger(__name__)


class FormattedException(Exception):
    pass


def _format_exception(error, filename):
    """Format the exception :error: for the loaded python module :filename:.
    Does only print information that belong the loaded module itself.
    """
    exc_type, exc_value, exc_tb = sys.exc_info()
    tbs = traceback.extract_tb(exc_tb)

    start_at = 0
    for index, entry in enumerate(tbs):
        tb_file, tb_lineno, tb_func, tb_text = entry
        if tb_file == filename:
            start_at = index
            break

    if start_at == len(tbs) or start_at == 0:
        # the error is not inside the module itself: just return the exception
        start_at = len(tbs)

    tbs = tbs[start_at:]

    formatted = ''.join(
        traceback.format_list(tbs) +
        traceback.format_exception_only(exc_type, exc_value))

    return formatted.strip()


class Builtins(object):
    """Context manager to register builtin attributes.
    When leaving the context all registered builtins are removed.
    """
    def __init__(self):
        self._registered = []

    def register(self, name, value):
        if name in __builtins__:
            raise KeyError('%s is already registered')
        __builtins__[name] = value
        self._registered.append(name)

    def cleanup(self):
        for name in self._registered:
            __builtins__.pop(name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()


def _check_file_exists(path):
    if not os.path.exists(path):
        raise IOError(errno.ENOENT,
                      'No such file',
                      path)


def _load_module(cwd, filename):
    if cwd:
        abspath = os.path.join(cwd, filename)
    else:
        abspath = os.path.abspath(filename)

    # python >= 2.7: do not write out compiled config file
    sys.dont_write_bytecode = True

    with chdir(cwd or os.path.dirname(filename)):
        _check_file_exists(abspath)

        name = abspath.replace('.', '_')
        try:
            return imp.load_source(name, abspath)
        except Exception as error:
            formatted = _format_exception(error, filename)
            raise FormattedException(formatted)


def load_registry_config_file(builtins, path, cwd=None):
    """Called within the Builtin context manager it loads the configuration
    of registries.

    :Registry: must be set as a builtin.
    """
    module = _load_module(cwd, path)
    for name in dir(module):
        value = getattr(module, name)
        if isinstance(value, Registry):
            _log.debug('found registry: %s', name)
            builtins.register(name, value)

    return module


def load_config_file(builtins, path, cwd=None):
    """Called within the Builtin context manager it loads the image build
    configuration module.

    :Registry: and :Image: must be set as builtins.
    """
    module = _load_module(cwd, path)
    for name in dir(module):
        value = getattr(module, name)
        if isinstance(value, BaseImageLayer):
            _log.debug('found image: %s', name)
            builtins.register(name, value)

    return module

