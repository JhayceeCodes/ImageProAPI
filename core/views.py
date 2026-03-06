from django.shortcuts import render

def home(request):
    return render(request, "index.html")

def api_docs(request):
    return render(request, "docs/api_docs.html")