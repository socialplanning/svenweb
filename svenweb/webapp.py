from sven.exc import *
try:
    from sven.backend import SvnAccess
except ImportError:
    SvnAccess = None
try:
    from sven.bzr import BzrAccess
except ImportError:
    BzrAccess = None
from webob import Request, Response, exc
import time, datetime

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

    def __init__(self, 
                 checkout_dir,
                 template_loader,
                 editor, viewer,
                 repo_type=None,
                 ):

        self.template_loader = template_loader

        self._checkout_dir = checkout_dir

        if repo_type == 'bzr':
            self.backend = BzrAccess
        else:
            self.backend = SvnAccess

        self.editor = editor

        self.viewer = viewer

    def checkout_dir(self, request):
        return self._checkout_dir
        
    def svn(self, request):
        return self.backend(self.checkout_dir(request))

    def get_response(self, template, data, content_type=None):
        data['mimetype'] = content_type = data.get('mimetype') or data.get('mimetype') or 'text/html'

        content = self.template_loader(template, data)
        content_type='text/html'
        res = Response(content_type=content_type, body=content)
        return res

    def __call__(self, environ, start_response):        
        request = Request(environ)
        request.path_info = request.path_info.rstrip('/')

        res = self.handle_request(request)
        return res(environ, start_response)

    def maybe_save(self, request):
        save = self.editor.match_save(request)
        if not save:
            return None

        contents, message, metadata, res = save(request)

        self.svn(request).write(request.path_info, 
                                contents, message, metadata=metadata)
        x = self.svn(request)
        uri = request.path_info
        return res

    def maybe_editform(self, request):
        try:
            content = self.svn(request).read(request.path_info)
            metadata = {}
        except NotAFile:
            return exc.HTTPBadRequest("Cannot edit directories")
        except NoSuchResource:
            return self.editor.new(request)

        x = self.svn(request)
        uri = request.path_info

        return self.editor.editform(request, content, metadata)

    def handle_request(self, request):
        if request.method == "POST":
            save = self.maybe_save(request)
            if save is not None: return save

        if request.method == "GET" and request.GET.get('view') == 'edit':
            edit = self.maybe_editform(request)
            if edit is not None: return edit

        if request.method == "HEAD" and not request.GET.get('view'):
            return self.default_view_head(request)

        if request.method != "GET":
            return exc.HTTPMethodNotAllowed("GET", "POST")

        if request.GET.get('view') == 'history':
            return self.history_view(request)

        if request.GET.get('view') == 'index':
            return self.index_view(request)

        return self.default_view(request)


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
            timestamp = obj['fields']['timestamp']
            from wsgiref.handlers import format_date_time
            obj['fields']['timestamp'] = \
                format_date_time(timestamp)
        contents = {'globs': contents}
        contents['title'] = request.path_info.rstrip('/')
        
        # put the raw form of the resource in the wsgi environment
        request.environ['svenweb.resource'] = dict(contents)

        if request.GET.has_key('atom'):
            return self.get_response('history.atom', contents, "application/atom+xml")
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

        uri = request.path_info

        prefix = request.script_name.rstrip('/')

        for item in contents:
            item['href'] = '/'.join((prefix, item['href'].lstrip('/')))

        contents = {'globs': contents,
                    'request': request}
        contents['title'] = request.path_info.rstrip('/')

        # put the raw form of the resource in the wsgi environment
        request.environ['svenweb.resource'] = dict(contents)

        return self.get_response('index.html', contents, "text/html")

    def default_view_head(self, request):
        version =request.GET.get('version', None)

        if request.path_info == '':
            request.path_info = '/'
            request.GET['view'] = 'index'
            return redirect(request)

        try:
            last_changed_rev = self.svn(request).last_changed_rev(request.path_info, version)
            if last_changed_rev and not version:
                # note: this case IS different from the ResourceUnchanged exception
                #       below, because here the redirect is temporary.
                # in fact, this can be considered the default behavior of the "default view"
                request.GET['version'] = str(last_changed_rev)
                if request.GET.has_key("latest-version"):
                    version = last_changed_rev
                else:
                    return redirect(request)
        except NotAFile:
            raise
            request.GET['view'] = 'index'
            return redirect(request)
        except NoSuchResource:
            return exc.HTTPNotFound()
            request.GET['view'] = 'edit'
            if request.GET.has_key('version'):
                del request.GET['version']
            return redirect(request)
        except ResourceUnchanged, e:
            request.GET['version'] = str(e.last_change)
            return redirect(request)

        res = Response()
        res.headers['X-Svenweb-Version'] = version
        return res

    def default_view(self, request):
        #default case (just a plain old view)
        version =request.GET.get('version', None)

        if request.path_info == '':
            request.path_info = '/'
            request.GET['view'] = 'index'
            return redirect(request)

        try:
            last_changed_rev = self.svn(request).last_changed_rev(request.path_info, version)
            if last_changed_rev and not version:
                # note: this case IS different from the ResourceUnchanged exception
                #       below, because here the redirect is temporary.
                # in fact, this can be considered the default behavior of the "default view"
                request.GET['version'] = str(last_changed_rev)
                if request.GET.has_key("latest-version"):
                    version = last_changed_rev
                else:
                    return redirect(request)
            data = self.svn(request).read(request.path_info, version)
        except NotAFile:
            request.GET['view'] = 'index'
            return redirect(request)
        except NoSuchResource:
            # We might have gotten here because the page 
            # did not yet exist at the given revision.
            # So, let's check whether it has any revisions
            # in the log at all.
            try:
                revs = self.svn(request).revisions(request.path_info)

            except NoSuchResource:
                # OK, it really doesn't exist.
                request.GET['view'] = 'edit'
                if request.GET.has_key('version'):
                    del request.GET['version']
                return redirect(request)

            # It does exist, at some point in the future.
            assert revs and len(revs)
            first_rev = revs[-1]
            error = "<h1>Page not yet born at revision %s</h1>" % version
            request.GET['version'] = first_rev
            redirected = redirect(request)
            error += "<div>Perhaps try <a href='%s'>its first revision</a> instead" % redirected.location
            return exc.HTTPNotFound(body=error)

        except ResourceUnchanged, e:
            request.GET['version'] = str(e.last_change)
            return redirect(request)

        except FutureRevision, e:
            error = "<h1>No such revision %s</h1>" % e.rev
            last_changed_rev = self.svn(request).last_changed_rev(request.path_info, version)
            request.GET['version'] = last_changed_rev
            redirected = redirect(request)
            error += "<div>Perhaps try <a href='%s'>its last revision</a> instead" % redirected.location
            return exc.HTTPNotFound(body=error)

        contents = {'contents': data}
        mimetype = "text/html"

        view = self.viewer.match_view(request, data, mimetype)
        if view:
            return view(request, data)

        contents['prev_href'] = "%s?version=%d" % (request.path_info,
                                                   int(
                request.GET['version']) - 1)

        x = self.svn(request)
        uri = request.path_info

        contents['format'] = request.GET.get('format')

        res = Response(
            content_type=mimetype,
            body=data)
        res.content_length = len(res.body)

        res.headers['X-Svenweb-Version'] = version

        return res
