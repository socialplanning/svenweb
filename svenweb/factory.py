from svenweb.webapp import SvnWikiView
from paste.httpexceptions import HTTPExceptionHandler

from pkg_resources import iter_entry_points

from svenweb.template_loader import TempitaLoader

def factory(global_conf, **app_conf):
    """create a webob view and wrap it in middleware"""
    key_str = 'svenweb.'
    args = dict([(key.split(key_str, 1)[-1], value)
                 for key, value in app_conf.items()
                 if key.startswith(key_str) ])

    templates_dir = args['templates_dir']
    template_loader = TempitaLoader(templates_dir)

    del args['templates_dir']

    app = SvnWikiView(
        template_loader=template_loader, 
        **args)

    return HTTPExceptionHandler(app)
