from django.urls import path
from .views import register_view, login_view, forgot_password, reset_password
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("forgot-password/", forgot_password, name="forgot_password"),
    path("reset-password/<str:token>/", reset_password, name="reset_password"),
]
