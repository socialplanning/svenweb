from sven.exc import *
from sven.backend import SvnAccess
from sven.bzr import BzrAccess
from pkg_resources import iter_entry_points
from webob import Request, Response, exc
from tempita import Template
import simplejson

def qs(dict):
    qs = ''
    for key, value in dict.items():
        if value == '':
            qs += '%s&' % key
        else:
            qs += '%s=%s&' % (key, value)
    qs = qs.rstrip('&')
    return qs

def redirect(req, perm=False):
    qstr = qs(req.GET)
    path = req.script_name + req.path_info + "?" + qstr
    if perm:
        return exc.HTTPMovedPermanently(location=path)
    return exc.HTTPTemporaryRedirect(location=path)

class SvnWikiView(object):
    def __init__(self, checkout_dir, templates_dir,
                 repo_type=None,
                 config_loader=None):
        self.response_functions = { 'GET': self.get,
                                    'POST': self.post,
                                    }
        self.views = {'edit': self.edit_view,
                      'history': self.history_view,
                      'index': self.index_view,
                      '': self.default_view,
                      }

        if not templates_dir.endswith('/'):
            templates_dir += '/'
        self.templates_dir = templates_dir
        self.checkout_dir = checkout_dir

        if repo_type == 'bzr':
            self.backend = BzrAccess
        else:
            self.backend = SvnAccess

    def svn(self, request):
        return self.backend(self.checkout_dir)

    ### methods dealing with HTTP
    def __call__(self, environ, start_response):        
        request = Request(environ)
        request.path_info = request.path_info.rstrip('/')
        res = self.make_response(request)
        return res(environ, start_response)
                                
    def make_response(self, request):
        return self.response_functions.get(request.method, self.error)(request)

    def get_response(self, template, data, content_type=None):
        #if template != 'edit.html':
        #    return Response(body=data['body'],
        #                    content_type=data.get('mimetype',
        #                                          'text/html'))

        data['mimetype'] = content_type = data.get('mimetype') or 'text/html'

        if template != 'view.html':
            content = Template.from_filename(self.templates_dir + template)
            content = content.substitute(**data)
            content_type='text/html'
            res = Response(content_type=content_type, body=content)
        else:
            body = data['body']
            body = body.replace('\n', "<br/>")
            body += "<div><a href='?view=edit'>edit file</a></div>"
            res = Response(content_type='text/html', body=body)

        res.content_length = len(res.body)
        return res

    def get(self, request):
        """
        return response to a GET requst
        """
        for view in self.views:
            if request.GET.get('view') == view:
                return self.views[view](request)
        return self.views[''](request)

    def post(self, request):
        """
        return response to a POST request
        """
        contents = request.POST.get('svenweb.resource_body')
        #if contents is None:
        #    return exc.HTTPForbidden('WTH?')

        message = request.POST.get('svenweb.commit_message')
        kind = request.POST.get('svenweb.mimetype')

        if request.GET.has_key('factory'):
            title = request.GET.get('factory')
            if not title:
                import random
                title = random.randint(0, 1000000)
            uri = '/'.join((request.path_info, str(title)))
            self.svn(request).write(uri, contents, message, kind)
            return exc.HTTPSeeOther(location=request.path_info)

        try:
            self.svn(request).write(request.path_info, contents, message, kind)
        except NotAFile:
            if kind:
                self.svn(request).set_kind(request.path_info, kind, message)
            else:
                import random
                title = random.randint(0, 1000000)
                uri = '/'.join((request.path_info, str(title)))
                self.svn(request).write(uri, contents, message, kind)
                #return exc.HTTPBadRequest("Cannot edit directories")

        return exc.HTTPSeeOther(location=request.path_info)

    def error(self, request):
        """deal with non-supported methods"""
        return exc.HTTPMethodNotAllowed("Only %r operations are allowed" % self.response_functions.keys())

    def edit_view(self, request):
        try:
            contents = self.svn(request).read(request.path_info)
        except NotAFile: #return exc.HTTPBadRequest("Cannot edit directories")
            return self.get_response("<form method='post'><input type='text' name='svenweb.resource_kind' value='%s'></input><input type='submit' value='Submit'></input></form>" %
                                     self.svn(request).kind(request.path_info),
                                     "text/html")
        except NoSuchResource:
            # this is not great
            # .. should treat this as an AddView on the directory
            # .. and the directory should be allowed to have a "new page" template perhaps
            parent = request.path_info.split('/')
            parent.pop()
            parent = '/'.join(parent)
            # end(notgreat)
            
            contents = {'body':'',
                        'mimetype':self.svn(request).kind(parent),
                        }        

        contents['mimetype'] = self.svn(request).kind(request.path_info)
        kind = contents.get('mimetype')
        
        # put the raw form of the resource in the wsgi environment
        request.environ['svenweb.resource'] = dict(contents)

        return self.get_response('edit.html', contents, "text/html")

    def history_view(self, request):
        version = request.GET.get('version', None)
        try:
            contents = self.svn(request).log(request.path_info, version)
        except NoSuchResource:
            request.GET['view'] = 'edit'
            return redirect(request)
        except ResourceUnchanged, e:
            request.GET['version'] = str(e.last_change)
            return redirect(request, perm=True)

        for obj in contents:
            obj['full_href'] = request.script_name + obj['href']
        contents = {'globs': contents}
        contents['title'] = request.path_info.rstrip('/')
        
        # put the raw form of the resource in the wsgi environment
        request.environ['svenweb.resource'] = dict(contents)
        return self.get_response('history.html', contents, "text/html")

    def index_view(self, request):
        version =request.GET.get('version', None)
        try:
            contents = self.svn(request).ls(request.path_info, version)
        except NotADirectory:
            request.GET.clear()
            return redirect(request)
        except ResourceUnchanged, e:
            request.GET['version'] = str(e.last_change)
            return redirect(request, perm=True)

        contents = {'globs': contents}
        contents['title'] = request.path_info.rstrip('/')

        # put the raw form of the resource in the wsgi environment
        request.environ['svenweb.resource'] = dict(contents)

        return self.get_response('index.html', contents, "text/html")

    def default_view(self, request):
        #default case (just a plain old view)
        version =request.GET.get('version', None)

        if request.path_info == '':
            request.GET['view'] = 'index'
            return redirect(request)

        try:
            last_changed_rev = self.svn(request).last_changed_rev(request.path_info, version)
            if last_changed_rev and not version:
                # note: this case IS different from the ResourceUnchanged exception
                #       below, because here the redirect is temporary.
                # in fact, this can be considered the default behavior of the "default view"
                request.GET['version'] = str(last_changed_rev)
                return redirect(request)
            contents = self.svn(request).read(request.path_info, version)
        except NotAFile:
            request.GET['view'] = 'index'
            return redirect(request)
        except NoSuchResource:
            request.GET['view'] = 'edit'
            if request.GET.has_key('version'):
                del request.GET['version']
            return redirect(request)
        except ResourceUnchanged, e:
            request.GET['version'] = str(e.last_change)
            return redirect(request)
        
        contents['prev_href'] = "%s?version=%d" % (request.path_info,
                                                   int(request.GET['version']) - 1)

        contents['title'] = request.path_info.rstrip('/')
        contents['format'] = request.GET.get('format')

        contents['mimetype'] = 'text/plain'

        # put the raw form of the resource in the wsgi environment
        request.environ['svenweb.resource'] = dict(contents)
        
        return self.get_response('view.html', contents, 'text/html')

