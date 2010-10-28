from svenweb.read import Renderer

from contenttransformer.app import FileTypeTransformer
from contenttransformer.web import parse_transforms

def filter_factory(global_conf, transforms=None, **app_conf):

    transforms = transforms or ''
    transforms = parse_transforms(transforms)

    def filter(app):
        return Renderer(app, 
                        Xformer(transforms))

    return filter

class Xformer(object):
    def __init__(self, transforms):
        self.transformer = FileTypeTransformer(*transforms)

    def match_view(self, req, content, mimetype):
        path = req.url
        transformer = self.transformer.match(path)
        if transformer is None:
            return None

        def render(req, content):
            return transformer(content)
        return render
