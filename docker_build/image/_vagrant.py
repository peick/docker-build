from ._base import FixBuildfileImageLayer
from .. import _vagrant_driver


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
