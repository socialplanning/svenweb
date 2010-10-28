converters = {}

def register(_from, to, func):
    converters.setdefault(_from, {})[to] = func

def get_conversions(_from):
    return converters.get(_from, {})

def convert(_from, to, content):
    return converters[_from][to](content)

import docutils.core
def rst2html(content):
    settings = {}
    parts = docutils.core.publish_parts(content,
                                        writer_name='html',
                                        settings_overrides=settings) 
    return parts['body']
    
register('text/plain+rst', 'text/html', rst2html)
