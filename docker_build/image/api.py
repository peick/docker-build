from ._vagrant import VagrantLayer
from ._rootfs import RootFSLayer
from ._docker import (
    BaseImageLayer,
    DockerfileDirectImageLayer,
    DockerfileImageLayer,
    NativeDockerImageLayer)


def _create_image(repotag=None, **kwargs):
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
        self._images = []

    def __iter__(self):
        for image in self._images:
            yield image

    def __len__(self):
        return len(self._images)

    def add(self, *args, **kwargs):
        image = _create_image(*args, **kwargs)
        self._images.append(image)
        return image

    @property
    def root_images(self):
        images = []
        for image in self._images:
            if image.is_root():
                images.append(image)
        return images

    def _tagged_images(self, images):
        tagged = []
        for image in images:
            if not image.is_temporary():
                tagged.append(image)
            tagged.extend(self._tagged_images(image.children))
        return tagged

    def tagged_images(self):
        return self._tagged_images(self.root_images)

