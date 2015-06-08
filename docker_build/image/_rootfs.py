from ._base import BaseImageLayer


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
