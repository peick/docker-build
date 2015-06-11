import requests
from ._compat import urlparse, urlunparse, to_ascii
from . import _docker_driver


class RegistryURL(object):
    def __init__(self, url=None, scheme=None, host=None, port=None, username=None, password=None, path=None):
        if url:
            if scheme or host or port or username or password:
                raise ValueError('url is already set.')

            if not url.startswith('http://') and not url.startswith('https://'):
                parsed   = urlparse('//' + url)
            else:
                parsed   = urlparse(url)
                scheme   = parsed.scheme
            host     = parsed.hostname
            port     = parsed.port
            username = parsed.username
            password = parsed.password
            path     = parsed.path

            if parsed.query:
                raise ValueError('query in url is not supported')
            if parsed.params or parsed.fragment:
                raise ValueError('params/fragment in url are not supported')

        if not host:
            raise ValueError('missing hostname')

        if password and not username:
            raise ValueError('password is set without a username')

        self._scheme   = scheme or 'http'
        self._host     = host
        self._port     = port
        self._username = username
        self._password = password
        self._path     = path or ''


    @property
    def auth(self):
        if self._username:
            return (self._username, self._password)

    @property
    def url(self):
        return self._url(with_auth=False, with_scheme=True)

    @property
    def docker_url(self):
        """URL compatible with the docker command line tool.
        """
        return self._url(with_auth=False, with_scheme=False)

    def _url(self, with_auth=True, with_scheme=True):
        if self._username and self._password and with_auth:
            netloc = '%s:%s@%s' % (self._username, self._password, self._host)
        else:
            netloc = self._host
        if self._port:
            netloc = '%s:%d' % (netloc, self._port)

        scheme = self._scheme if with_scheme else None

        url = urlunparse([
            to_ascii(scheme),
            to_ascii(netloc),
            to_ascii(self._path),
            None,
            None,
            None])

        if not scheme:
            if url.startswith(b'//'):
                url = url[2:]
        return url

    def repotag_url(self, repotag):
        return '%s/%s' % (self.docker_url, repotag)

    def tag_url(self, repotag):
        if ':' in repotag:
            repo, tag = repotag.split(':', 1)
        else:
            repo = repotag
            tag  = 'latest'

        return '%s/v1/repositories/%s/tags/%s' % (self.url, repo, tag)


class Registry(RegistryURL):
    def __init__(self, *args, **kwargs):
        super(Registry, self).__init__(*args, **kwargs)

        self._logged_in = False

        self._http = requests.session()
        if self._username:
            self._http.auth = self.auth

        self._docker_driver = _docker_driver


    def _check_logged_in(self):
        if self._logged_in:
            return

        if self._username:
            raise Exception('Not logged in')

    def _login(self):
        if self._logged_in:
            return

        if not self._username:
            return

        self._docker_driver.login(self.url, self._username, self._password)
        self._logged_in = True

    def _logout(self):
        if not self._logged_in:
            return

        self._docker_driver.logout(self.url)
        self._logged_in = False

    def __enter__(self):
        self._login()

    def __exit__(self, exc_type, exc_value, traceback):
        self._logout()

    # -------------------------------------------------------------------------

    def ping(self):
        url = '%s/v1/_ping' % (self.url, )
        self._http.get(url)

    def delete_tag(self, repotag):
        # remove tag from remote image
        self._check_logged_in()
        url = self.tag_url(repotag)
        self._http.delete(url)

    def post(self, image, repotag):
        self._check_logged_in()
        url = self.repotag_url(repotag)
        self._docker_driver.tag(image, url)
        self._docker_driver.push(url)

    def info(self, repotag):
        url = self.tag_url(repotag)
        response = self._http.get(url)
        if response.ok:
            return response.json()

    def repositories(self):
        """Fetch a list of repositories.
        """
        url = '%s/v1/search' % (self.url, )
        response = self._http.get(url)
        if not response.ok:
            raise Exception(response)
        data = response.json()

        repositories = []
        for item in data['results']:
            repositories.append(item['name'])
        return repositories

    def images(self):
        """Fetch a list of images.
        """
        repositories = self.repositories()

        images = []
        for repo in repositories:
            url = '%s/v1/repositories/%s/tags' % (self.url, repo)
            response = self._http.get(url)
            if not response.ok:
                raise Exception(response)
            data = response.json()

            for tag in data.keys():
                image = '%s:%s' % (repo, tag)
                images.append(self.repotag_url(image))
        return images


class RegistryCollection(object):
    def __init__(self):
        self.registries = []

    def add(self, *args, **kwargs):
        registry = Registry(*args, **kwargs)
        self.registries.append(registry)
        return registry
