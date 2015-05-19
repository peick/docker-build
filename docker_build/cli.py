from optparse import OptionParser
import errno
import functools
import os
import sys
import tempfile
import logging

from _exec import ExecutionError
from _registry import RegistryCollection
from _image import ImageCollection, BaseImageLayer
from _load_config import Builtins, load_config_file, load_registry_config_file, FormattedException


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
        help    = 'Docker registry url, e.g. https://foo:bar@localhost:5000',
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

    options, _args = parser.parse_args(args)

    _fix_default_cli_arguments(options)

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
    # TODO use force option
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
                load_registry_config_file(filename)

            # load image description
            if options.dockerbuild == '-':
                dockerbuild = sys.stdin.read()
                with tempfile.NamedTemporaryFile(delete=True) as temp:
                    temp.write(dockerbuild)
                    temp.flush()
                    bound_load_config_file(temp.name, cwd=cwd)
            else:
                bound_load_config_file(options.dockerbuild)

    except FormattedException, error:
        _log.error(error.args[0])
        sys.exit(1)
    except IOError, error:
        if error.errno == errno.ENOENT:
            _log.error('%s: %s', error.strerror, error.filename)
            sys.exit(1)
        raise

    if not image_collection.images:
        print >>sys.stderr, "No images defined."
        sys.exit(1)

    if options.check_only:
        return

    if options.list_images:
        for image in image_collection.images:
            is_uploaded = image.is_uploaded()
            present = '+' if is_uploaded else '-'
            print present, image.full_repotag
        sys.exit(0)

    # build images and upload to registry
    cleanup = []
    retval = None
    for image in image_collection.images:
        _log.info('Building image: %s', image.full_repotag)
        try:
            image.build()
            cleanup.append(image)
            image.upload_to_registry()
        except ExecutionError, error:
            _log.error('While building image %s. %s', image.full_repotag, error)
            retval = 1
            break

    _log.debug('cleanup temporary images')
    for image in cleanup:
        try:
            image.cleanup()
        except Exception, error:
            _log.error(error)
            retval = 1

    if retval:
        sys.exit(1)


if __name__ == '__main__':
    main()
