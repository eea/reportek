from django.shortcuts import render


def spabundle(request):
    return render(request, 'bundle.html')
