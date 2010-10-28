from svenweb.webapp import SvnWikiView
from paste.httpexceptions import HTTPExceptionHandler

from pkg_resources import iter_entry_points

from svenweb.template_loader import TempitaLoader
from hyperbmp.read import HbmpView

from svenweb.edit import BaseEditor
from svenweb.read import BaseReader

from hyperbmp.edit import HbmpEditor

def factory(global_conf, editor=None, viewer=None, **app_conf):
    """create a webob view and wrap it in middleware"""
    key_str = 'svenweb.'
    args = dict([(key.split(key_str, 1)[-1], value)
                 for key, value in app_conf.items()
                 if key.startswith(key_str) ])

    templates_dir = args['templates_dir']
    template_loader = TempitaLoader(templates_dir)

    del args['templates_dir']

    editor = editor or BaseEditor
    editor = editor(template_loader)

    viewer = viewer or BaseReader
    viewer = viewer()
    
    app = SvnWikiView(
        template_loader=template_loader,
        editor=editor,
        viewer=viewer,
        **args)

    return HTTPExceptionHandler(app)
