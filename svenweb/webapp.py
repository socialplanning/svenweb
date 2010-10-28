from sven.exc import *
from sven.backend import SvnAccess
from sven.bzr import BzrAccess
from pkg_resources import iter_entry_points
from webob import Request, Response, exc

import simplejson
import mimetypes

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

class EditView(object):

    def __init__(self, template_loader):
        self.template_loader = template_loader

    def new_default_mimetype(self, request):
        return mimetypes.guess_type(request.path_info)[0] or 'text/html'

    def post(self, request):
        """
        return response to a POST request
        """
        contents = request.POST.get('svenweb.resource_body')
        #if contents is None:
        #    return exc.HTTPForbidden('WTH?')

        message = request.POST.get('svenweb.commit_message')
        mimetype = request.POST.get('svenweb.mimetype')

        return (contents, message, mimetype,
                exc.HTTPSeeOther(location=request.path_info))

    def match_save(self, request):
        """
        return a callable that takes a request and returns
        (contents, commit_message, mimetype, webob.Response)
        """
        if request.method == "POST":
            return self.post

    def match_edit(self, request):
        """
        returns a callable that takes a (webob.Request, content, mimetype)
        and returns a webob.Response
        """
        if request.method == "GET" and request.GET.get('view') == 'edit':
            return self.form

    def form(self, request, content, mimetype):
        content = self.template_loader('edit.html', dict(body=content,
                                                         mimetype=mimetype
                                                         ))
        content_type='text/html'
        return Response(content_type=content_type, body=content)

    def new(self, request):
        mimetype = self.new_default_mimetype(request) 
        content = self.template_loader('edit.html', dict(body='',
                                                         mimetype=mimetype
                                                         ))
        return Response(content_type='text/html', body=content)
    
class HbmpView(object):

    default = {'height': 16, 'width': 16, 
               'pixelheight': '50px', 'pixelwidth': '50px',}

    def pixelheight(self, req):
        if req.GET.has_key('ph'):
            return req.GET['ph']

        return self.default['pixelheight']

    def pixelwidth(self, req):
        if req.GET.has_key('pw'):
            return req.GET['pw']

        return self.default['pixelwidth']

    def parse(self, content):
        rows = []
        for line in content.split('\n'):
            if not line.strip():
                continue
            row = [i.strip() for i in line.split(',')]
            if rows:
                assert len(row) == len(rows[-1]), "This doesn't look like a valid bitmap; the rows aren't all the same length."
            rows.append(row)
        return rows

    def match_view(self, request, content, mimetype):
        """
        returns a callable that takes (request, content)
        and returns a Response
        """
        if mimetype == 'text/csv+hbmp':
            return self.render

    def render(self, req, content):
        html = """
<table style='border: 1px solid black;
              border-collapse: collapse;'>"""
        data = self.parse(content)
        for row in data:
            html += "<tr>"
            for item in row:
                item = item.split('>')
                #assert len(item) == 1 or len(item) == 2, "Bad cell format"
                if len(item) == 2:
                    item, link = item
                elif len(item) == 1:
                    item = item[0]
                    link = None

                if not link:
                    html += """
<td class='%s' height='%s' width='%s' 
    style='padding: 0; border: 1px solid black; background-color: %s'>
""" % (
                        item,
                        self.pixelheight(req),
                        self.pixelwidth(req),
                        item)
                else:
                    html += """
<td href='%s' class='%s' height='%s' width='%s' 
    style='padding: 0; border: 1px solid black; background-color: %s'>
""" % (
                        link,
                        item,
                        self.pixelheight(req),
                        self.pixelwidth(req),
                        item)
                    html += "<center><a href='%s'>&nbsp;</a></center>" % link

                html += "&nbsp;</td>"

            html += "</tr>"
        html += "</table>"
        return Response(html)

class SvnWikiView(object):

    def __init__(self, 
                 checkout_dir,
                 template_loader,
                 repo_type=None,
                 ):

        self.template_loader = template_loader

        self.checkout_dir = checkout_dir

        if repo_type == 'bzr':
            self.backend = BzrAccess
        else:
            self.backend = SvnAccess

        self.editor = EditView(template_loader)

        self.viewer = HbmpView()

    def svn(self, request):
        return self.backend(self.checkout_dir)

    ### methods dealing with HTTP
    def __call__(self, environ, start_response):        
        request = Request(environ)
        request.path_info = request.path_info.rstrip('/')

        res = self.handle_request(request)
        return res(environ, start_response)

    def handle_request(self, request):
        save = self.editor.match_save(request)
        if save:
            contents, message, mimetype, res = save(request)
            
            self.svn(request).write(request.path_info, 
                                    contents, message, mimetype)

            return res

        edit = self.editor.match_edit(request)
        if edit:
            try:
                q = self.svn(request).read(request.path_info)
                content = q['body']
                mimetype = q['mimetype']
            except NotAFile:
                return exc.HTTPBadRequest("Cannot edit directories")
            except NoSuchResource:
                return self.editor.new(request)
            return edit(request, content, mimetype)

        if request.method != "GET":
            return exc.HTTPMethodNotAllowed("GET", "POST")

        views = {'history': self.history_view,
                 'index': self.index_view,
                 }

        for view in views:
            if request.GET.get('view') == view:
                return views[view](request)

        return self.default_view(request)

    def get_response(self, template, data, content_type=None):
        #if template != 'edit.html':
        #    return Response(body=data['body'],
        #                    content_type=data.get('mimetype',
        #                                          'text/html'))

        data['mimetype'] = content_type = data.get('mimetype') or data.get('mimetype') or 'text/html'

        if template != 'view.html':
            content = self.template_loader(template, data)
            content_type='text/html'
            res = Response(content_type=content_type, body=content)
        elif content_type == 'text/html':
            body = data['body']
            body = body.replace('\n', "<br/>")
            body += "<div><a href='?view=edit'>edit file</a></div>"
            res = Response(content_type=content_type, body=body)
        else:
            res = Response(content_type=content_type, body=data['body'])

        res.content_length = len(res.body)
        return res

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
        
        content = contents['body']
        mimetype = contents['mimetype']

        view = self.viewer.match_view(request, content, mimetype)
        if view:
            return view(request, content)

        contents['prev_href'] = "%s?version=%d" % (request.path_info,
                                                   int(
                request.GET['version']) - 1)

        contents['title'] = request.path_info.rstrip('/')
        contents['format'] = request.GET.get('format')

        return self.get_response('view.html', contents, contents['mimetype'] or 'text/html')
