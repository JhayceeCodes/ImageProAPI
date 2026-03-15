from django.shortcuts import render

def home(request):
    return render(request, "index.html")

def api_docs(request):
    return render(request, "docs/api_docs.html")

def playground(request):
    return render(request, "playground.html")

def login_page(request):
    return render(request, "auth/login.html")

def register_page(request):
    return render(request, "auth/register.html")
