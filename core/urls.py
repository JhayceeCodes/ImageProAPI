from django.urls import path
from .views import home, api_docs, playground, login_page, register_page

urlpatterns = [
    path("", home, name="home"),
    path("api/documentation/", api_docs, name="api-docs"),
    path("playground/", playground, name="playground"),
    path("login/", login_page, name="login-page"),
    path("register/", register_page, name="register-page"),
]
