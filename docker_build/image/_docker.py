import functools
import logging
import tempfile

from .._compat import to_utf8
from ._base import BaseImageLayer, FixBuildfileImageLayer


_log = logging.getLogger(__name__)


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
        self._deletable = False

    def _build(self):
        if not self._base:
            self._pull()
        else:
            self._image_id = self._base._image_id

        if self._base and not self._registry:
            self._driver.tag(self._image_id, self.repotag)

    def _pull(self):
        inspection = self._driver.inspect_id(self.full_repotag)
        if inspection is None:
            self._driver.pull(self.full_repotag)
            inspection = self._driver.inspect_id(self.full_repotag)

        assert inspection
        self._image_id = inspection

