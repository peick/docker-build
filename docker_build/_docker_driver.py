import json
import logging
import os
import re

from . import _exec


_log = logging.getLogger(__name__)


def _exec_docker_cmd(command, *args, **kwargs):
    return _exec.exec_cmd('docker', command, *args, **kwargs)


def build(repotag, chdir=None):
    """Executes ``docker build``.
    """
    output = _exec_docker_cmd('build', '--rm', '-t', repotag, '.', chdir=chdir)
    match = re.search(r'Successfully built ([0-9a-fA-F]{12,})', output)
    if match:
        return match.group(1)
    raise Exception()


def commit(container_id, repotag=None):
    """Executes ``docker commit <container> [repotag]`` and return the
    docker image id.
    """
    if repotag:
        args = [repotag]
    else:
        args = []
    return _exec_docker_cmd('commit', '-p', container_id, *args)


def import_(filename):
    # raise IOError if file does not exist
    os.path.getsize(filename)
    return _exec_docker_cmd('import', '-', stdin=filename)


def inspect(container_id, format=None):
    """Executes ``docker inspect <container|image> ...``.
    """
    if format:
        args = ['-f', format]
    else:
        args = []
    args.append(container_id)

    _status, output = _exec_docker_cmd('inspect', *args, can_fail=True)
    if not _status:
        if not format:
            data = json.loads(output)
            assert isinstance(data, list)
            assert len(data) == 1
            data = data[0]
            assert isinstance(data, dict)
            return data
        return output


def inspect_id(what):
    return inspect(what, '{{.Id}}').strip()


def login(registry, username, password, email=' '):
    """Executes ``docker login ...``.
    """
    _exec_docker_cmd(
        'login', '-u', username, '-p', password, '-e', email, registry)


def logout(registry):
    """Executes ``docker logout <registry>``.
    """
    _exec_docker_cmd('logout', registry)


def pull(repotag):
    """Executes ``docker pull <repotag>``.
    """
    _exec_docker_cmd('pull', repotag)


def push(repotag):
    """Executes ``docker push <repotag>``.
    """
    assert repotag
    _exec_docker_cmd('push', repotag)


def rm(container_id, force=True):
    """Executes ``docker rm``.
    """
    if force:
        return _exec_docker_cmd('rm', container_id, '-f', can_fail=True)[0]
    else:
        _exec_docker_cmd('rm', container_id)


def rmi(repotag, force=True):
    """Executes ``docker rmi``.
    """
    if force:
        while True:
            status, output = _exec_docker_cmd(
                'rmi', '-f', repotag, can_fail=True)
            if not status:
                _log.debug('>> ' + output)
            if status:
                break
        return status
    else:
        _exec_docker_cmd('rmi', repotag)


#def run(repotag, cmd, volumes=()):
#    """Executes ``docker run`` and returns the docker container id.
#    """
#    args = []
#    for vol in volumes:
#        args.append('-v')
#        args.append(vol)
#    args.append(cmd)
#
#    _exec_docker_cmd('run', repotag, *args)


def tag(image, repotag):
    """Executes ``docker tag <image> <repotag>``.
    """
    assert image
    assert repotag
    _exec_docker_cmd('tag', image, repotag)
