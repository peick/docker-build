import errno
import functools
import getpass
import logging
import os
import random
import re
import string
import tempfile

from . import _docker_driver, _vagrant_driver
from ._compat import to_utf8
from ._temp import TempDirectory, TempFileLink
from ._exec import chdir


_REPO_TAG_PATTERN = r'(%(user)s/)?%(repo)s(:%(tag)s)?' % \
    dict(user=r'[a-z0-9_.-]+',
         repo=r'[a-z0-9_.-]+',
         tag=r'[a-z0-9_.-]+')

# name of temporary images
_DEFAULT_TEMP_REPO = 'temp_image/%(username)s:%(uniq_id)s'

_log = logging.getLogger(__name__)


def _uniq_id(length):
    assert length >= 1
    abc    = string.ascii_lowercase
    abc123 = string.ascii_lowercase + string.digits
    id_    = random.sample(abc, 1) \
           + [random.sample(abc123, 1)[0] for i in range(length - 1)]

    return ''.join(id_)


def _expand_repotag(repotag_template):
    username = getpass.getuser()
    id16 = _uniq_id(16)
    id30 = _uniq_id(30)
    uniq_id = _uniq_id(30 - 1 - len(username))
    template_data = {
        'username': username,
        'uniq_id': uniq_id,
        'uniq_id16': id16,
        'uniq_id30': id30
    }
    return repotag_template % template_data


class BaseImageLayer(object):
    """
    :repotag: Repository and tag of the image.
    :base: Base image. It's either a valid docker repository+tag string or
        an instance of a BaseImageLayer.
    """
    def __init__(self,
        repotag=None,
        registry=None,
        base=None,
        temp_repotag_template=_DEFAULT_TEMP_REPO,
        cwd=None):

        self._cwd = cwd or os.getcwd()

        if repotag is None:
            repotag = _expand_repotag(temp_repotag_template)
            self._is_temporary = True
            # assert not registry
        else:
            self._is_temporary = False

        match = re.match(_REPO_TAG_PATTERN, repotag)
        assert match, 'Invalid repository/tag name: %s' % repotag

        self.repotag = repotag
        self._registry = registry
        self._base = base

        self._driver = _docker_driver
        self._already_built = False
        self._image_id = None

        if registry and not self._is_temporary:
            self.full_repotag = registry.repotag_url(repotag)
        else:
            self.full_repotag = repotag


    def _commit(self, container_id):
        self._image_id = self._driver.commit(container_id, self.repotag)


    def build(self):
        """Build docker image.
        """
        if not self._already_built:
            if self._base:
                # recursively build dependency images
                self._base.build()
            with chdir(self._cwd):
                self._build()
            self._already_built = True


    def _build(self):
        """Underlying docker image build implementation.
        """
        raise NotImplementedError(self.repotag, self.__class__._build)


    def cleanup(self):
        """Remove temporary image.
        """
        if self._is_temporary:
            self._driver.rmi(self.repotag, force=True)

    def upload_to_registry(self):
        assert self._already_built
        if self._is_temporary:
            return
        if not self._registry:
            return

        with self._registry:
            self._registry.delete_tag(self.repotag)
            self._registry.post(self._image_id, self.repotag)

    def is_uploaded(self):
        if self._is_temporary:
            return
        if not self._registry:
            inspection = self._driver.inspect(self.repotag)
            return inspection is not None

        return self._registry.info(self.repotag) is not None


class FixBuildfileImageLayer(BaseImageLayer):
    """Some tools builds images based on build files with fix names, e.g.
    docker uses Dockerfile, vagrant uses Vagranfile.
    """
    def __init__(self, dir_or_file, basename, **kwargs):
        super(FixBuildfileImageLayer, self).__init__(**kwargs)
        self._basename = basename

        dir_or_file = os.path.join(self._cwd, dir_or_file)
        if os.path.isdir(dir_or_file):
            self._filename = os.path.join(dir_or_file, basename)
        else:
            self._filename = dir_or_file

        if not os.path.exists(self._filename):
            raise IOError(errno.ENOENT, 'No such file', self._filename)

    def _build(self):
        directory = os.path.dirname(self._filename)

        if os.path.basename(self._filename) == self._basename:
            self._build_directory(directory)
        else:
            temp_buildfile = os.path.join(directory, self._basename)

            with TempFileLink(self._filename, temp_buildfile):
                self._build_directory(directory)

    def _build_directory(self, directory):
        raise NotImplementedError()


class DockerfileImageLayer(FixBuildfileImageLayer):
    """Use a Dockerfile to build an image.

    The dockerfile can be either a path that contains the Dockerfile or the
    path to the Dockerfile, either named Dockerfile or differently.
    """
    def __init__(self, dockerfile, **kwargs):
        assert 'base' not in kwargs
        assert 'temp_repotag_template' not in kwargs
        super(DockerfileImageLayer, self).__init__(
            dockerfile, 'Dockerfile', **kwargs)

    def _build_directory(self, directory):
        self._image_id = self._driver.build(self.repotag, chdir=directory)


class DockerfileDirectImageLayer(BaseImageLayer):
    def __init__(self, **kwargs):
        image_kwargs = {}
        for key, _fn in self.FIELDS:
            key = key.lower()
            if key in kwargs:
                value = kwargs.pop(key)
                image_kwargs[key] = value

        self._rest_kwargs = kwargs
        self._kwargs = image_kwargs
        super(DockerfileDirectImageLayer, self).__init__(**kwargs)
        assert self._base

    def _content(self):
        content = []

        for field_name, field_fn in self.FIELDS:
            value = field_fn(self)
            if not isinstance(value, list):
                value = [value]
            for v in value:
                if v is not None:
                    content.append('%s %s' % (field_name, v))

        return to_utf8('\n'.join(content))

    def _build(self):
        with tempfile.NamedTemporaryFile(delete=True, dir=self._cwd) as temp:
            content = self._content()
            _log.debug(content)
            temp.file.write(content)
            temp.file.flush()

            kwargs = self._rest_kwargs.copy()
            kwargs.pop('base')
            kwargs.pop('temp_repotag_template', None)
            image = DockerfileImageLayer(temp.name, **kwargs)
            image.build()
            self._image_id = image._image_id

    def _FROM(self):
        return self._base._image_id

    def _field_value(self, key):
        return self._kwargs.get(key)

    FIELDS = [
        ('FROM',   _FROM),
        ('RUN',    functools.partial(_field_value, key='run')),
        ('CMD',    functools.partial(_field_value, key='cmd')),
        ('EXPOSE', functools.partial(_field_value, key='expose')),
        ('EXEC',   functools.partial(_field_value, key='exec')),
    ]


class NativeDockerImageLayer(BaseImageLayer):
    """Uses an existing image. The image is pulled from a private registry
    or from the official docker registry if the image is not already present.
    """
    def __init__(self, repotag, registry=None, base=None):
        assert repotag, "Missing repotag"
        super(NativeDockerImageLayer, self).__init__(
            repotag=repotag, registry=registry, base=base)


    def _build(self):
        if not self._base:
            self._pull()
        else:
            self._image_id = self._base._image_id

        if self._base and not self._registry:
            self._driver.tag(self._image_id, self.repotag)

    def _pull(self):
        fmt = '{{.Id}}'

        inspection = self._driver.inspect(self.full_repotag, format=fmt)
        if inspection is None:
            self._driver.pull(self.full_repotag)
            inspection = self._driver.inspect(self.full_repotag, format=fmt)

        assert inspection
        self._image_id = inspection


class RootFSLayer(BaseImageLayer):
    """Import a root file system from an archive file into a docker image.

    Supported archives are (see ``docker import``):
        * tar
        * tar.gz
        * tar.bz2
        * tar.xz
    """
    def __init__(self, rootfs, pre=None, post=None, **kwargs):
        super(RootFSLayer, self).__init__(**kwargs)
        self._rootfs = rootfs
        self._pre = pre
        self._post = post

    def _build(self):
        if self._pre:
            exitcode = self._pre()
            if exitcode:
                raise Exception('Pre action failed (exitcode: %s)' % exitcode)
        try:
            self._image_id = self._driver.import_(self._rootfs)
        finally:
            if self._post:
                self._post()


class VagrantLayer(FixBuildfileImageLayer):
    """Use vagrant with docker provider. Runs provisioners to customize the
    vagrant box. Creates a docker image by calling ``docker commit`` from
    the running vagrant box.

    :dir_or_file: is either a directory that contains the file :Vagrantfile:
    or a file.

    The docker base image used within vagrant should be prepared for use with
    ssh in order to call provisioners.
    """
    def __init__(self, dir_or_file, **kwargs):
        super(VagrantLayer, self).__init__(dir_or_file, 'Vagrantfile', **kwargs)
        self._vagrant_driver = _vagrant_driver

    def _build_directory(self, directory):
        with self._vagrant_driver.vagrant(directory) as container_id:
            self._commit(container_id)

# -----------------------------------------------------------------------------

def create_image(repotag=None, **kwargs):
    kwargs['repotag'] = repotag

    if kwargs.get('rootfs'):
        return RootFSLayer(kwargs.pop('rootfs'), **kwargs)
    elif kwargs.get('vagrant'):
        return VagrantLayer(kwargs.pop('vagrant'), **kwargs)
    elif kwargs.get('dockerfile'):
        return DockerfileImageLayer(kwargs.pop('dockerfile'), **kwargs)
    elif set(kwargs.keys()) & (set(['cmd', 'expose', 'run'])):
        return DockerfileDirectImageLayer(**kwargs)
    elif set(kwargs.keys()).issubset(set(['repotag', 'registry', 'base'])):
        return NativeDockerImageLayer(**kwargs)
    else:
        raise Exception('Invalid image parameter: %s' % kwargs)


class ImageCollection(object):
    def __init__(self):
        self.images = []

    def add(self, *args, **kwargs):
        image = create_image(*args, **kwargs)
        self.images.append(image)
        return image

