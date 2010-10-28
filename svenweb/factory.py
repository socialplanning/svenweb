from svenweb.webapp import SvnWikiView
from paste.httpexceptions import HTTPExceptionHandler

from pkg_resources import iter_entry_points

def factory(global_conf, **app_conf):
    """create a webob view and wrap it in middleware"""
    key_str = 'svenweb.'
    args = dict([(key.split(key_str, 1)[-1], value)
                 for key, value in app_conf.items()
                 if key.startswith(key_str) ])

    app = SvnWikiView(**args)

    return HTTPExceptionHandler(app)
