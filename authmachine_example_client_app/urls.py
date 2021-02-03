from django.urls import path

from authmachine_example_client_app import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login", views.LoginView.as_view(), name="login"),
    path("logout", views.LogoutView.as_view(), name="logout"),
    path("oidc-callback", views.OIDCallbackView.as_view(), name="auth_callback"),
    path("oidc-logout-callback", views.OIDLogoutCallbackView.as_view(), name="auth_logout_callback"),
]
