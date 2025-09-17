from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('contact/send/', views.ContactFormView.as_view(), name='contact_send'),
    path('admin-login/', views.AdminLoginView.as_view(), name='admin_login'),
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]