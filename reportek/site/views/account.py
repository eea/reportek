from django.shortcuts import render


def workspace(request, path):
    return render(request, "workspace.html", {
        "path": path,
    })
