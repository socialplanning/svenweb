from svenweb.webapp import SvnWikiView

class SvenwebFarm(object):
    def __init__(self, template_loader, editor, viewer, repo_type=None):
        self.template_loader = template_loader
        self.editor = editor
        self.viewer = viewer
        self.repo_type = repo_type

    def checkout_dir(self, environ):
        return environ['HTTP_X_SVENWEB_DIR']

    def __call__(self, environ, start_response):
        checkout_dir = self.checkout_dir(environ)
        app = SvnWikiView(checkout_dir,
                          self.template_loader,
                          self.editor, self.viewer,
                          self.repo_type)
        return app(environ, start_response)

from webob import Request
from svenweb.edit import BaseEditor
from svenweb.read import BaseReader
from svenweb.template_loader import TempitaLoader
def factory(global_conf, **app_conf):
    args = app_conf
    templates_dir = args['templates_dir']
    template_loader = TempitaLoader(templates_dir)
    del args['templates_dir']

    app = SvenwebFarm(template_loader, 
                      BaseEditor(template_loader), BaseReader(),
                      'bzr')

    if global_conf.get("debug") == "true":
        
        def middleware(environ, start_response):
            req = Request(environ)
            environ['HTTP_X_SVENWEB_DIR'] = '/tmp/' + req.GET['repo']
            return app(environ, start_response)

        return middleware
    return app
