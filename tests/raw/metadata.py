base_image = Image('test/base')

Image('test/sample_cmd', cmd='echo $USER', base=base_image)

Image('test/sample_expose', expose='22', base=base_image)

Image('test/sample_maintainer', run='bash /install.sh', base=base_image)
