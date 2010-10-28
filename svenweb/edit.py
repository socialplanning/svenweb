import mimetypes
from webob import exc
from webob import Response

from svenweb.lib import location

class BaseEditor(object):
    """
    Required:

     new_default_mimetype(self, request)
      -> mime_string

     match_save(self, request)
      -> callable or None

     match_edit(self, request)
      -> callable or None
      
     save callable (request)
      -> content, commit_message, mimetype, response
    
     edit callable (request, current_content, current_mimetype)
      -> response

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
        (contents, commit_message, mimetype, webob.Response)
        """
        if request.method == "POST":
            return self.post

    def match_edit(self, request, content, mimetype):
        """
        returns a callable that takes a (webob.Request, content, mimetype)
        and returns a webob.Response
        """
        if request.method == "GET" and request.GET.get('view') == 'edit':
            return self.form

    def post(self, request):
        """
        return response to a POST request
        """
        contents = request.POST.get('svenweb.resource_body')

        message = request.POST.get('svenweb.commit_message')
        mimetype = request.POST.get('svenweb.mimetype')
        
        loc = location(request)
        return (contents, message, mimetype,
                exc.HTTPSeeOther(location=loc))

    def form(self, request, content, mimetype):
        content = self.template_loader('edit.html', dict(body=content,
                                                         mimetype=mimetype
                                                         ))
        return Response(content_type='text/html', body=content)

    def new(self, request):
        mimetype = self.new_default_mimetype(request) 
        content = self.template_loader('edit.html', dict(body='',
                                                         mimetype=mimetype
                                                         ))
        return Response(content_type='text/html', body=content)
    

