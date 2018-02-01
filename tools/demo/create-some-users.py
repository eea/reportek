#!/usr/bin/env python
import os
import sys


REPORTERS = {
    "DE": "german",
    "RO": "romanian",
    "SE": "swedish",
}


def mkreporters():
    from reportek.roles.models import ReporterUser
    from reportek.core.models import Reporter

    for abbr, name in REPORTERS.items():
        reporter = Reporter.objects.get(abbr=abbr)
        user = ReporterUser.objects.create_user(
            name,
            password=name,
            reporter=reporter,
        )


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "reportek.site.settings")
    try:
        import django
    except ImportError:
        raise ImportError(
            "Couldn't import Django. "
            "Did you activate the virtual environment?"
        )

    imported = False
    try:
        import reportek
        imported = True
    except ImportError:
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(1, cwd)
            try:
                import reportek
                imported = True
            except ImportError:
                pass
    if not imported:
        raise ImportError(
            "Couldn't import Reportek modules. Make sure you activated "
            "the virtual environment and you are running this from the "
            "repository root (or that `reportek` is in your PYTHONPATH)."
        )

    django.setup()
    mkreporters()
