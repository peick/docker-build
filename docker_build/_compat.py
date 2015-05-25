try:
    from urllib.parse import urlparse, urlunparse
except ImportError:
    from urlparse import urlparse, urlunparse


def to_utf8(value):
    if value is None or isinstance(value, bytes):
        return value
    return value.encode('utf-8')


def to_ascii(value):
    if value is None or isinstance(value, bytes):
        return value
    return value.encode('ascii')
