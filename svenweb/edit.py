import mimetypes
from webob import exc
from webob import Response

from svenweb.lib import location
from svenweb.convert import convert, get_conversions

class BaseEditor(object):
    """
    Required:

     new_default_mimetype(self, request)
      -> mime_string

     match_save(self, request)
      -> callable or None

     editform(request, content, mimetype)
      
     save callable (request)
      -> content, commit_message, mimetype, response
    
     new(self, request)
      -> response
    """
    def __init__(self, template_loader):
        self.template_loader = template_loader

    def new_default_mimetype(self, request):
        return mimetypes.guess_type(request.path_info)[0] or 'text/html'

    def match_save(self, request):
        """
        return a callable that takes a request and returns
        (contents, commit_message, metadata, webob.Response)
        """
        if request.method == "POST":
            if request.POST.has_key('convert'):
                return self.convert
            return self.post

    def editform(self, request, content, metadata):
        """
        returns a callable that takes a (webob.Request, content, mimetype)
        and returns a webob.Response
        """
        if request.method != "GET":
            return None
        if request.GET.get('view') != 'edit':
            return None

        return self.form(request, content, metadata)

    def convert(self, request):
        content = request.POST.get('svenweb.resource_body')

        mimetype = request.POST.get('svenweb.mimetype')
        _from = request.POST['convert_from']

        message = request.POST.get('svenweb.commit_message')

        loc = location(request)        
        return (convert(_from, mimetype, content),
                message, {'mimetype':mimetype},
                exc.HTTPSeeOther(location=loc))
        

    def post(self, request):
        """
        return response to a POST request
        """
        contents = request.POST.get('svenweb.resource_body')

        message = request.POST.get('svenweb.commit_message')
        mimetype = request.POST.get('svenweb.mimetype')
        metadata = {'mimetype': mimetype}

        loc = location(request)
        return (contents, message, metadata,
                exc.HTTPSeeOther(location=loc))

    def form(self, request, content, metadata):

        mimetype = metadata.get("mimetype")

        content = self.template_loader('edit.html', 
                                       dict(body=content,
                                            mimetype=mimetype,
                                            conversions=get_conversions(mimetype),
                                            ))
        return Response(content_type='text/html', body=content)

    def new(self, request):
        mimetype = self.new_default_mimetype(request) 
        content = self.template_loader('edit.html', dict(body='',
                                                         mimetype=mimetype,
                                                         ))
        return Response(content_type='text/html', body=content)
    

