import os
import sys
import logging
from collections import defaultdict
import pkgutil
import pyclbr
import base64
import xmlrpc.client
from functools import wraps
from importlib import import_module
from inspect import getmro
from traceback import print_tb
from lxml import etree

from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate, login

log = logging.getLogger('reportek.workflows')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


def on_import_error(name):
    error(f'Error importing module {name}')
    _type, value, traceback = sys.exc_info()
    print_tb(traceback)


def get_package_modules(path, name):
    """
    Walks a package's directory recursively, and returns a list of modules therein.
    """
    modules = []
    for _, mod_name, is_pkg in pkgutil.walk_packages(path, name + '.', onerror=on_import_error):
        if not is_pkg:
            modules.append(mod_name)
    return modules


def get_pkg_classes(path, name):
    """
    Builds and returns a dict of modules names in package `pkg`, and their classes.
    """
    classes = defaultdict(list)
    for mod in get_package_modules(path, name):
        module_classes = pyclbr.readmodule(mod)
        for cls_name in module_classes:
            classes[mod].append(cls_name)

    return classes


def get_based_classes(path, package, base_classes, skip_bases=True):
    """
    Identifies classes based on specified base classes in a package.

    Returns a set of tuples of the form:

        ```
        (reportek.core.models.workflows.<module>.<class>, <class>)
        ```

    The tuples are meant for model choice usage.
    """

    wf_classes = set()
    for mod, classes in get_pkg_classes(path, package).items():
        live_mod = import_module(mod)
        for cls_name in classes:
            # Skip base classes
            if skip_bases and cls_name in base_classes:
                continue
            cls = getattr(live_mod, cls_name)
            cls_ancestors = [cls.__name__ for cls in getmro(cls)]
            if any(base_cls in base_classes for base_cls in cls_ancestors):
                wf_classes.add(('.'.join([mod, cls_name]), cls_name))

    return wf_classes


def path_parts(path):
    # Courtesy of Python Cookbook
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def get_xsd_uri(file_path):
    try:
        tree = etree.parse(file_path)
    except etree.XMLSyntaxError:
        return None

    root = tree.getroot()
    try:
        return root.attrib[root.keys()[0]]
    except (AttributeError, IndexError):
        return None


def fully_qualify_url(url):
    if not url.startswith('/'):
        url = f'/{url}'
    proto = 'https' if settings.REPORTEK_USE_TLS else 'http'
    return f'{proto}://{settings.REPORTEK_DOMAIN}{url}'


def basic_auth_login(request):
    """
    Logs in the user if request came with BasicAuthentication
    Meant for usage with non-DRF views (where `authentication_classes` is available).
    """
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == 'basic':
                uname, passwd = base64.b64decode(auth[1]).decode('utf-8').split(':', 1)
                user = authenticate(username=uname, password=passwd)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        request.user = user

    return request


# https://github.com/m7v8/django-basic-authentication-decorator/blob/master/django_basic_auth.py


def view_or_basicauth(view, request, test_func, realm='', *args, **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    if test_func(request.user):
        # Already logged in, just return the view.
        #
        return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials
    #
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            # NOTE: We are only support basic authentication for now.
            #
            if auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).decode('utf-8').split(':', 1)
                user = authenticate(username=uname, password=passwd)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        request.user = user
                        if test_func(request.user):
                            return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    #
    response = HttpResponse()
    response.status_code = 401
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response


def logged_in_or_basicauth(realm=''):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.
    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.
    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.
    The purpose of this is that in several django projects I have needed
    several specific views that need to support basic authentication, yet the
    web site as a whole used django's provided authentication.
    The uses for this are for urls that are access programmatically such as
    by rss feed readers, yet the view requires a user to be logged in. Many rss
    readers support supplying the authentication credentials via http basic
    auth (and they do NOT support a redirect to a form where they post a
    username/password.)
    Use is simple:
    @logged_in_or_basicauth()
    def your_view:
        ...
    You can provide the name of the realm to ask for authentication within.
    """
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.is_authenticated(),
                                     realm, *args, **kwargs)
        return wrapper
    return view_decorator


def has_perm_or_basicauth(perm, realm=''):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.
    Use:
    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...
    """
    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.has_perm(perm),
                                     realm, *args, **kwargs)
        return wrapper
    return view_decorator


def log_xmlrpc_errors(logger):
    def log_decorator(f):
        """
        Method wrapper, ensures logging of XMLRPC faults and protocol errors.
        """
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            try:
                return f(self, *args, **kwargs)
            except xmlrpc.client.Fault as err:
                logger.error(f'XMLRPC fault: code={err.faultCode}, error={err.faultString}')
            except xmlrpc.client.ProtocolError as err:
                logger.error(f'XMLRPC protocol error: url={err.url}, headers={err.headers}, '
                             f'code={err.errcode}, msg={err.errmsg}')
        return wrapper
    return log_decorator


def bin_to_str(bin_obj, encoding='utf-8'):
    """
    Converts a xmlrpc.client.Binary object to string.
    """
    try:
        return str(bin_obj.data, encoding)
    except Exception:
        return 'ERROR: could not decode'


def get_content_encoding(result):
    """
    Extracts the encoding from a content_type string
    (e.g. 'text/html;charset=UTF-8').
    """
    _result = result.split(';')
    if len(_result) < 2 or not 'charset=' in _result[1]:
        return None
    else:
        enc = _result[1].split('=')
        if len(enc) < 2:
            return None
        return enc[1]
