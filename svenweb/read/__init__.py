from webob import Request

class BaseReader(object):
    """
    Required:

     match_view(self, request, body, mimetype)
     -> callable or None

     read callable (request, body)
     -> webob.Response
    """
    def match_view(self, request, content, mimetype):
        return False

class Renderer(object):
    def __init__(self, app, *renderers):
        self.app = app
        self.renderers = renderers

    def __call__(self, environ, start_response):
        req = Request(environ)
        res = req.get_response(self.app)
        body = res.body
        mimetype = res.content_type

        for renderer in self.renderers:
            render = renderer.match_view(req, body, mimetype)
            if render is not None:
                return render(req, body)(environ, start_response)

        return res(environ, start_response)

