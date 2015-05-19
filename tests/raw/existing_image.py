# our private registry. Create one with
#   $ docker run --rm -e SEARCH_BACKEND=sqlalchemy -p 5000:5000 -e STORAGE_PATH=/registry registry:0.9.1
registry = Registry('localhost:5000')

# pulls image registry:latest from the official docker registry and uploads
# it to the registry on localhost:5000 as 'my-registry:latest'
registry_image = Image('registry:0.9.1')
my_registry_image = Image('my-registry:latest', base=registry_image, registry=registry)

# tag an image
Image('your-registry', base=registry_image)

