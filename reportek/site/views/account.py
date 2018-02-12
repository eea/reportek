from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def workspace(request, path=''):
    return render(request, "workspace.html", {
        "path": path,
    })
