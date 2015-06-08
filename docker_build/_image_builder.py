import logging
from ._exec import ExecutionError


_log = logging.getLogger(__name__)


class ImageBuilder(object):
    """Builds images and uploads them to the registry (optionally).

    Does not build images if they are already built unless options.force
    is set.
    """
    def __init__(self, options, image_collection):
        self._options = options
        self._image_collection = image_collection


    def _images(self):
        cleanup = []
        retval = None

        tagged = self._image_collection.tagged_images()

        if not tagged:
            _log.warn('Only temporary images found. Nothing to build.')
            return

        build = []
        if self._options.force:
            for image in tagged:
                image.delete()
                build.append(image)
        else:
            for image in tagged:
                if not image.is_uploaded():
                    build.append(image)

            if not build:
                _log.info('All images are up to date.')
                return

        return build


    def build(self):
        images = self._images()
        if not images:
            return True

        try:
            for image in images:
                _log.info('Building image: %s', image.full_repotag)
                try:
                    # builds dependent images, too
                    image.build()
                    image.upload_to_registry()
                except ExecutionError as error:
                    _log.error(
                        'While building image %s. %s', image.full_repotag, error)
                    return False
        finally:
            _log.debug('cleanup temporary images')
            self._cleanup()

        return True


    def _cleanup(self):
        for image in self._image_collection:
            image.cleanup()

