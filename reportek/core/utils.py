import sys
import logging
from collections import defaultdict
import pkgutil
import pyclbr
from importlib import import_module
from inspect import getmro
from traceback import print_tb

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
