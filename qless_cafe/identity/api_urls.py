from django.urls import path

from .api_views import CsrfView
from .api_views import LoginView
from .api_views import LogoutView
from .api_views import MeView
from .api_views import SignupView

urlpatterns = [
    path("csrf/", CsrfView.as_view(), name="csrf"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
