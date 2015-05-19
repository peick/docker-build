import pytest
from docker_build._registry import Registry


@pytest.mark.parametrize('url, expect, auth', [
    ('example.com',             'http://example.com',          None),
    ('user:pwd@example.com',    'http://example.com',          ('user', 'pwd')),
    ('user:pwd@example.com:81', 'http://example.com:81',       ('user', 'pwd')),
    ('https://example.com',     'https://example.com',         None),
    ('example.com:81/pa/th',    'http://example.com:81/pa/th', None)
])
def test_registry_url(url, expect, auth):
    registry = Registry(url)
    assert registry.url == expect
    assert registry.auth == auth


@pytest.mark.parametrize('kwargs, expect, auth', [
    (dict(host='example.com'),
     'http://example.com',
     None),

    (dict(host='example.com', username='user', password='pwd'),
     'http://example.com',
     ('user', 'pwd')),

    (dict(host='example.com', username='user', password='pwd', port=81),
     'http://example.com:81',
     ('user', 'pwd')),

    (dict(host='example.com', scheme='https'),
     'https://example.com',
     None),

    (dict(host='example.com', port=81, path='pa/th'),
     'http://example.com:81/pa/th',
     None)
])
def test_registry_kwargs(kwargs, expect, auth):
    registry = Registry(**kwargs)
    assert registry.url == expect
    assert registry.auth == auth

