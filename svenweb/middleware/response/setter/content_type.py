def get_mimetype(backend, uri):
    """
    returns the content's mimetype metaprop or None

    TODO: rev=None param (needs work in sven)
    """
    return backend.mimetype(uri) or None

def filter_factory(global_conf, checkout_dir, repo_type=None,
                   default_content_type=None):
    def filter(app):
        return ForceContentType(app, checkout_dir, repo_type,
                                default_content_type)
    return filter

from webob import Request

from sven.backend import SvnAccess
from sven.bzr import BzrAccess

class ForceContentType(object):

    def __init__(self, app, checkout_dir, repo_type=None,
                 default_content_type=None):
        self.app = app
        self.checkout_dir = checkout_dir

        if repo_type == 'bzr':
            self.backend_factory = BzrAccess
        else:
            self.backend_factory = SvnAccess

        self.default_content_type = default_content_type

    def get_backend(self):
        return self.backend_factory(self.checkout_dir)

    def __call__(self, environ, start_response):
        req = Request(environ)
        path_info = req.path_info

        res = req.get_response(self.app)

        if res.status_int == 200:
            backend = self.get_backend()
            content_type = get_mimetype(backend, path_info)
            if not content_type:
                content_type = self.default_content_type
            if content_type:
                res.content_type = content_type

        return res(environ, start_response)
