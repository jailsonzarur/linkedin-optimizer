from django.contrib.auth import views as auth_views
from django.urls import path

from accounts.forms import LoginForm
from accounts.views import home, signup

app_name = "accounts"

urlpatterns = [
    path("", home, name="home"),
    path(
        "sign-in/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("sign-out/", auth_views.LogoutView.as_view(), name="logout"),
    path("sign-up/", signup, name="signup"),
]
