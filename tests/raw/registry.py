registry = Registry('usEr:pAss@registry.example.com:5000')

Image('foox/example:1.2', registry=registry, vagrant='vagrant.py.Vagrantfile')
