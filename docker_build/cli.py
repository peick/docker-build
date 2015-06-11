from __future__ import print_function
from optparse import OptionParser
import errno
import functools
import os
import re
import sys
import tempfile
import logging

from .image.api import ImageCollection
from ._exec import ExecutionError
from ._registry import RegistryCollection
from ._image_builder import ImageBuilder
from ._load_config import (
    Builtins,
    load_config_file,
    load_registry_config_file,
    FormattedException)


_MAIN_FILENAME     = 'docker-build.images'
_REGISTRY_FILENAME = ['docker-build.registry',
                      '~/.docker-build/registry',
                      '/etc/docker-build/registry']

_log = logging.getLogger(__name__)


def _get_cli_arguments(args=None):
    parser = OptionParser()
    parser.add_option('-v', '--verbose',
        dest    = 'verbose',
        action  = 'count',
        default = 0)
    parser.add_option('-r', '--registry',
        help    = 'Docker registry url, e.g. qa=https://foo:bar@localhost:5000',
        metavar = 'URL',
        dest    = 'registry',
        action  = 'append',
        default = [])
    parser.add_option('--rc',
        help    = 'Docker registry configuration file. Default search path is' \
            '%s. This option can be applied multiple times.' \
            % ', '.join(_REGISTRY_FILENAME),
        metavar = 'PATH',
        dest    = 'registry_config',
        action  = 'append',
        default = [])
    parser.add_option('-c',
        help    = 'Filename to the build file. Defaults to %s. If set to "-",' \
            ' then configuration is read from standard input.' % _MAIN_FILENAME,
        metavar = 'PATH',
        dest    = 'dockerbuild',
        default = _MAIN_FILENAME)
    parser.add_option('-C', '--check-config',
        help    = 'Check configuration file only. Does not build images',
        dest    = 'check_only',
        action  = 'store_true',
        default = False)
    parser.add_option('-l', '--list',
        help    = 'List images to be build',
        dest    = 'list_images',
        action  = 'store_true',
        default = False)
    parser.add_option('-f', '--force-recreate',
        help    = 'Rebuild / Recreates images if already exists. Default ' \
            'is to not build images that already exist.',
        dest    = 'force',
        action  = 'store_true',
        default = False)
    parser.add_option('--list-registry-images',
        help    = 'List images of a registry',
        dest    = 'registry_list_images')

    options, _args = parser.parse_args(args)

    _fix_default_cli_arguments(options)

    for desc in options.registry:
        if not re.match(r'[a-zA-Z_][a-zA-Z0-9_]*=.*', desc):
            parser.error('-r %s must be in format <name>=<url>' % desc)

    return options


def _fix_default_cli_arguments(options):
    if not options.registry_config:
        for path in _REGISTRY_FILENAME:
            if os.path.exists(path):
                options.registry_config.append(path)
                break


def _configure_logging(options):
    if options.verbose >= 2:
        level = logging.DEBUG
    elif options.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARN
    log_format = '%(asctime)-15s [%(levelname)s] %(message)s'
    logging.basicConfig(level=level, format=log_format)


def main(args=None):
    options = _get_cli_arguments(args)
    _configure_logging(options)

    image_collection = ImageCollection()
    registry_collection = RegistryCollection()

    try:
        cwd = os.getcwd()

        with Builtins() as builtins:

            bound_load_registry_config_file = \
                functools.partial(load_registry_config_file, builtins)
            bound_load_config_file = \
                functools.partial(load_config_file, builtins)

            builtins.register('Registry', registry_collection.add)
            builtins.register('Image', image_collection.add)
            builtins.register('load_registry_config_file', bound_load_registry_config_file)
            builtins.register('load_config_file', bound_load_config_file)

            # optional: load registries
            for filename in options.registry_config:
                bound_load_registry_config_file(filename)

            # optional: load registries directly from command line
            for desc in options.registry:
                name, url = desc.split('=', 1)
                registry = registry_collection.add(url)
                builtins.register(name, registry)

            if options.registry_list_images:
                # variables are injected into builtins
                registry = __builtins__[options.registry_list_images]
                for repotag in registry.images():
                    print(repotag)
                return

            # load image description
            if options.dockerbuild == '-':
                dockerbuild = sys.stdin.read()
                with tempfile.NamedTemporaryFile(delete=True) as temp:
                    temp.write(dockerbuild.encode('utf-8'))
                    temp.flush()
                    bound_load_config_file(temp.name, cwd=cwd)
            else:
                bound_load_config_file(options.dockerbuild)

    except FormattedException as error:
        _log.error(error.args[0])
        sys.exit(1)
    except IOError as error:
        if error.errno == errno.ENOENT:
            _log.error('%s: %s', error.strerror, error.filename)
            sys.exit(1)
        raise

    if not len(image_collection):
        print("No images defined.", file=sys.stderr)
        sys.exit(1)

    if options.check_only:
        return

    if options.list_images:
        for image in image_collection.tagged_images():
            is_uploaded = image.is_uploaded()
            present = '+' if is_uploaded else '-'
            print(present, image.full_repotag)
        sys.exit(0)


    builder = ImageBuilder(options, image_collection)
    retval = builder.build()

    if not retval:
        sys.exit(1)


if __name__ == '__main__':
    main()
