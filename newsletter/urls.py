from django.urls import path
from . import views

app_name = 'newsletter'

urlpatterns = [
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('unsubscribe/<uuid:token>/', views.UnsubscribeView.as_view(), name='unsubscribe'),
    path('confirm/<uuid:token>/', views.ConfirmSubscriptionView.as_view(), name='confirm'),
    
    # Admin views
    path('admin/dashboard/', views.NewsletterDashboardView.as_view(), name='admin_dashboard'),
    path('admin/send/<int:campaign_id>/', views.SendNewsletterView.as_view(), name='send_newsletter'),
    path('admin/test/<int:campaign_id>/', views.SendTestEmailView.as_view(), name='send_test_email'),
    path('admin/subscribers/', views.ManageSubscribersView.as_view(), name='manage_subscribers'),
    path('admin/subscribers/add/', views.AddSubscriberView.as_view(), name='add_subscriber'),
    path('admin/subscribers/edit/<int:subscriber_id>/', views.EditSubscriberView.as_view(), name='edit_subscriber'),
    path('admin/subscribers/unsubscribe/<int:subscriber_id>/', views.UnsubscribeSubscriberView.as_view(), name='unsubscribe_subscriber'),
    path('admin/subscribers/bulk-action/', views.BulkActionView.as_view(), name='bulk_action'),
    path('admin/create-campaign/', views.CreateCampaignView.as_view(), name='create_campaign'),
    path('admin/delete-campaign/<int:campaign_id>/', views.DeleteCampaignView.as_view(), name='delete_campaign'),
]