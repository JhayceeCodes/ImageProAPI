from django.urls import path
from .views import home, api_docs, playground

urlpatterns = [
    path("", home, name="home"),
    path("api/documentation/", api_docs, name="api-docs"),
    path("playground/", playground, name="playground"),
]
