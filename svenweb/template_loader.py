
from tempita import Template
class TempitaLoader(object):
    def __init__(self, templates_dir):
        if not templates_dir.endswith('/'):
            templates_dir += '/'
        self.templates_dir = templates_dir

    def __call__(self, template_name, context):
        content = Template.from_filename(self.templates_dir + template_name)
        return content.substitute(**context)
