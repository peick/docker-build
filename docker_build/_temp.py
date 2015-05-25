import os
import shutil
import tempfile


class TempFileLink(object):
    """Context manager that creates a symbolic link and removes it on exit.
    """
    def __init__(self, path, link):
        self._path = path
        self._link = link

    def __enter__(self):
        assert not os.path.exists(self._link), self._link
        os.symlink(self._path, self._link)

    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(self._link)


class TempDirectory(object):
    """Context manager that creates a temporary directory.
    """
    def __init__(self):
        self._temp = None

    def __enter__(self):
        return self.create()

    def __exit__(self, exc_type, exc_value, traceback):
        self.delete()

    def create(self):
        assert self._temp is None
        self._temp = tempfile.mkdtemp()
        return self._temp

    def delete(self):
        assert self._temp
        shutil.rmtree(self._temp)

