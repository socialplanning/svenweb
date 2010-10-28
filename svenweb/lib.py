def location(request):
    location = '/'.join((request.script_name.rstrip('/'),
                         request.path_info.lstrip('/')))
    return location
