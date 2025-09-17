from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    # Password reset flow for admin
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-code/', views.VerifyResetCodeView.as_view(), name='verify_code'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
]