from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("me/", views.MeView.as_view(), name="auth-me"),
]
