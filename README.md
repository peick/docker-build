Docker-build is a command line tool for building docker images and uploading
them to the registry. It extends the low level '''docker build''' by building
images with a Dockerfile, Vagrantfile or a rootfs archive.

Once built the image can be uploaded to a registry, which could be the official
docker registry or your private registry.


Sample build and upload
=======================

    $ docker-build

**docker-build.images** and optionally **docker-build.registry** file must exist in the
current working directory.

Alternatively you can set the image build file with:

    $ docker-build -c my-images.config

The image configuration itself are pure python scripts with special meanings for builtin members *Image* and *Registry*. An *Image* can be one of:

 * a native docker image. The already existing image is used as it is. If the image is not present locally it's pulled from the global registry or the defined registry:
    Image('hello-world')
    Image('hello-world', registry=my_registry)
 * an image that uses an existing Dockerfile. The filename can differ from Dockerfile.
 * an image that uses an existing Vagrantfile with docker as provider.
 * an image created from an archive (tar, tar.bz2, tar.gz, tar.xz) that contains a root filesystem.

Listing image before building them:

    $ docker-build -l

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

    # file: docker-build.registries
    staging = Registry('https://foo:bar@localhost:5000')
    qa      = Registry(user='foo', password='bar', host='localhost', port=5001)


Examples
========

ssh-server with a Dockerfile
----------------------------

    #!docker-build -c
    #
    # file: docker-build.images
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
    # file: docker-build.images
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
    # file: docker-build.images
    #
    # Use vagrant for provisioning a docker image

    Image('my-ubuntu-vg', vagrant='vagrant.Vagrantfile')

build from root filesystem
--------------------------

    #!docker-build -c
    #
    # file: docker-build.images
    #
    # Use an existing root filesystem in a (packed) tar file to create a
    # docker image.

    def build_rootfs():
        return os.system('make -f rootfs.makefile all')

    def clean_rootfs():
        return os.system('make -f rootfs.makefile dist-clean')

    # anonymous image
    root_image = Image(rootfs='rootfs.tar', pre=build_rootfs, post=clean_rootfs)

    Image('my-app', cmd='/opt/my-app/bin/app', base=root_image)

