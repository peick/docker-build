Docker-build is a command line tool for building docker images and uploading
them to the registry. It extends the low level '''docker build''' by building
images with usual a Dockerfile, Vagrantfile or a rootfs.

Once built the image is uploaded to a registry, which could be the official
registry or your private registry.


Sample build and upload
=======================

    $ docker-build

docker-build.images and optionally docker-build.registry file must exist in the
current working directory.


Registry configuration
======================

There are two ways to configure registries. Either by command line argument
'''-r''' or in a registry configuration file.

    $ docker-build -r https://foo:bar@localhost:5000

    $ docker-build -r staging:localhost:5000

    $ docker-build --rc Dockerbuild.registries


Registry configuration file
---------------------------

Registries can be defined in the file '''docker-build.registry''' in the same
folder where the docker-build.images can be found or as global settings in one
of the pathes:

 * $HOME/.docker-build/registry
 * /etc/docker-build/registry

Example

    staging = Registry('https://foo:bar@localhost:5000')
    qa      = Registry(user='foo', password='bar', host='localhost', port=5001)


Examples
========

ssh-server with a Dockerfile
----------------------------

    #!docker-build -c
    #
    # use the ubuntu image from the official registry to create an image that
    # runs a ssh server
    ubuntu_image = Image('ubuntu')

    Image('my-ubuntu-ssh', base=ubuntu_image,
        run = ['apt-get install -y openssh-server',
               'mkdir -p /var/run/sshd'],
        cmd = '/usr/sbin/sshd -D -e',
        expose = 22)

    # another image using an existing Dockerfile that contains the same logic
    Image('my-ubuntu-ssh2', dockerfile = 'ssh-server.Dockerfile')


upload to registry
------------------

    #!docker-build -c
    #
    # Uploads official images to your private registry

    my_registry = Registry('localhost:5000')

    images = [
        Image('ubuntu:14.04'),
        Image('ubuntu:14.10'),
        Image('ubuntu:15.04')]

    for image in images:
        Image(image.repotag, base=image, registry=my_registry)

use vagrant for provisioning
----------------------------

    #!docker-build -c
    #
    # Use vagrant for provisioning a docker image

    Image('my-ubuntu-vg', vagrant='vagrant.Vagrantfile')

build from root filesystem
--------------------------

    #!docker-build -c
    #
    # Use an existing root filesystem in a (packed) tar file to create a
    # docker image.

    Image('my-app', rootfs='rootfs.tar')

