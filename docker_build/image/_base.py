import errno
import getpass
import logging
import os
import random
import re
import string

from .. import _docker_driver
from .._exec import chdir
from .._temp import TempDirectory, TempFileLink


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

        self.children = []
        self._cwd = cwd or os.getcwd()
        self._deletable = True

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

        if self._base:
            self._base.add_child(self)

        self._driver = _docker_driver
        self._already_built = False
        self._image_id = None

        if registry and not self._is_temporary:
            self.full_repotag = registry.repotag_url(repotag)
        else:
            self.full_repotag = repotag


    def is_root(self):
        return self._base is None


    def add_child(self, child_image):
        self.children.append(child_image)


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
        if self._is_temporary and self._already_built:
            self._driver.rmi(self.repotag, force=True)


    def upload_to_registry(self):
        if self._is_temporary:
            return
        if not self._registry:
            return

        assert self._already_built
        with self._registry:
            self._registry.delete_tag(self.repotag)
            self._registry.post(self._image_id, self.repotag)


    def is_uploaded(self):
        if self._is_temporary:
            return
        if not self._registry:
            image_id = self._driver.inspect_id(self.repotag)
            return image_id is not None

        return self._registry.info(self.repotag) is not None


    def is_temporary(self):
        return self._is_temporary


    def delete(self):
        if not self._deletable:
            return
        if not self.is_uploaded():
            return
        if self._registry:
            _log.warn('not supported yet.')
            return

        image_id = self._driver.inspect_id(self.repotag)
        self._driver.rmi(image_id)
        return True


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

