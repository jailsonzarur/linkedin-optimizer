from django.contrib.auth import views as auth_views
from django.urls import path

from accounts.forms import LoginForm
from accounts.views import home, signup

app_name = "accounts"

urlpatterns = [
    path("", home, name="home"),
    path(
        "entrar/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("criar-conta/", signup, name="signup"),
]
