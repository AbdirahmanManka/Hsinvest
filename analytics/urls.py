from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard_root'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    # Analytics URLs will be expanded later
]