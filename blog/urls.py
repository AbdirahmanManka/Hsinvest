from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('tag/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('create/', views.CreatePostView.as_view(), name='create_post'),
    path('edit/<int:pk>/', views.EditPostView.as_view(), name='edit_post'),
    path('rate/<int:post_id>/', views.RatePostView.as_view(), name='rate_post'),
    path('comment/<int:post_id>/', views.AddCommentView.as_view(), name='add_comment'),
    
    # Admin-only URLs
    path('admin/posts/', views.AdminPostListView.as_view(), name='admin_post_list'),
    path('admin/comments/', views.AdminCommentListView.as_view(), name='admin_comment_list'),
    path('admin/stats/', views.AdminPostStatsView.as_view(), name='admin_post_stats'),
    path('admin/post/<int:post_id>/delete/', views.AdminDeletePostView.as_view(), name='admin_delete_post'),
    path('admin/comment/<int:comment_id>/delete/', views.AdminDeleteCommentView.as_view(), name='admin_delete_comment'),
    path('admin/comment/<int:comment_id>/approve/', views.AdminApproveCommentView.as_view(), name='admin_approve_comment'),
]