sub = load_config_file('sub/settings.py')

# reference to an existing docker image
Image('test/%d' % sub.a)
