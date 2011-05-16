from svenweb.webapp import SvnWikiView

class SvenwebFarm(SvnWikiView):
    def __init__(self, base_checkout_dir,
                 template_loader,
                 editor, viewer, 
                 repo_type=None):
        SvnWikiView.__init__(self, base_checkout_dir, template_loader,
                             editor, viewer, repo_type=repo_type)
        
    def checkout_dir(self, request):
        return '/'.join((
                self._checkout_dir.rstrip('/'),
                request.environ['HTTP_X_SVENWEB_DIR'].lstrip('/'),
                ))

from webob import Request
from svenweb.edit import BaseEditor
from svenweb.read import BaseReader
from svenweb.template_loader import TempitaLoader
def factory(global_conf, **app_conf):
    args = app_conf
    templates_dir = args['templates_dir']
    template_loader = TempitaLoader(templates_dir)
    del args['templates_dir']

    basedir = args['base_checkout_dir']
    
    app = SvenwebFarm(
        basedir,
        template_loader, 
        BaseEditor(template_loader), BaseReader(),
        'bzr')

    if global_conf.get("debug") == "true":
        
        def middleware(environ, start_response):
            req = Request(environ)
            environ['HTTP_X_SVENWEB_DIR'] = "test"
            return app(environ, start_response)

        return middleware
    return app
