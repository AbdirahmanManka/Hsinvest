from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View, CreateView, UpdateView, TemplateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, F, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from taggit.models import Tag
from .models import BlogPost, Category, Comment, Rating, BlogView
from analytics.models import PageView


def get_essential_categories():
    """Get the list of essential categories for HasilInvest blog"""
    return [
        # Original categories
        {'name': 'Technology', 'description': 'Technology and programming articles', 'order': 1},
        {'name': 'Lifestyle', 'description': 'Personal development and lifestyle tips', 'order': 2},
        {'name': 'Business', 'description': 'Business and entrepreneurship insights', 'order': 3},
        {'name': 'Education', 'description': 'Learning and educational content', 'order': 4},
        {'name': 'Health & Wellness', 'description': 'Health and wellness advice', 'order': 5},
        {'name': 'Islamic Banking', 'description': 'Islamic banking principles and practices', 'order': 6},
        {'name': 'Islamic Finance', 'description': 'Islamic financial instruments and markets', 'order': 7},
        {'name': 'Banking in Islam', 'description': 'Islamic banking concepts and Shariah compliance', 'order': 8},
        {'name': 'Financial Advice', 'description': 'Personal and Islamic financial guidance', 'order': 9},
        
        # New HasilInvest categories
        {'name': 'Personal Finance', 'description': 'Personal financial planning and money management', 'order': 10},
        {'name': 'Investing', 'description': 'Investment strategies and market insights', 'order': 11},
        {'name': 'Stock Market', 'description': 'Stock market analysis and trading insights', 'order': 12},
        {'name': 'Halal Investments', 'description': 'Shariah-compliant investment opportunities', 'order': 13},
        {'name': 'Real Estate', 'description': 'Real estate investment and market trends', 'order': 14},
        {'name': 'Entrepreneurship', 'description': 'Starting and growing your own business', 'order': 15},
        {'name': 'Career Development', 'description': 'Professional growth and career advancement', 'order': 16},
        {'name': 'Startups', 'description': 'Startup culture, funding, and innovation', 'order': 17},
        {'name': 'Innovation', 'description': 'Latest trends and innovative ideas', 'order': 18},
        {'name': 'Productivity', 'description': 'Tips and tools for increased productivity', 'order': 19},
        {'name': 'Leadership', 'description': 'Leadership skills and management insights', 'order': 20},
        {'name': 'Motivation', 'description': 'Motivational content and personal growth', 'order': 21},
        {'name': 'Mindset', 'description': 'Mental frameworks for success and growth', 'order': 22},
        {'name': 'Economy', 'description': 'Economic analysis and market trends', 'order': 23},
        {'name': 'Global Markets', 'description': 'International markets and global economics', 'order': 24},
        {'name': 'Tax & Zakat', 'description': 'Tax planning and Islamic Zakat guidance', 'order': 25},
        {'name': 'Retirement Planning', 'description': 'Planning for a secure financial future', 'order': 26},
        {'name': 'Wealth Management', 'description': 'Strategies for building and preserving wealth', 'order': 27},
        {'name': 'Crypto & Blockchain (Halal perspective)', 'description': 'Cryptocurrency and blockchain from Islamic viewpoint', 'order': 28},
        {'name': 'Sustainability & Green Finance', 'description': 'Sustainable investing and green financial products', 'order': 29},
    ]


def ensure_essential_categories():
    """Create any missing essential categories"""
    essential_categories = get_essential_categories()
    
    for cat_data in essential_categories:
        Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'order': cat_data['order'],
                'is_active': True
            }
        )


class PostListView(ListView):
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = BlogPost.objects.filter(
            status='published'
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')
        
        # Filter by category if specified in URL parameters
        category_slug = self.request.GET.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                queryset = queryset.filter(category=category)
            except Category.DoesNotExist:
                # If category doesn't exist, return empty queryset
                queryset = BlogPost.objects.none()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).order_by('order')
        
        # Get the current category for highlighting
        category_slug = self.request.GET.get('category')
        if category_slug:
            try:
                context['current_category'] = Category.objects.get(slug=category_slug, is_active=True)
            except Category.DoesNotExist:
                context['current_category'] = None
        else:
            context['current_category'] = None
        
        # Get popular tags - handle django-taggit properly
        try:
            # For django-taggit, get tags with usage count
            from django.db.models import Count
            context['popular_tags'] = Tag.objects.annotate(
                num_times=Count('taggit_taggeditem')
            ).order_by('-num_times')[:10]
        except Exception:
            # If any error occurs, provide empty list
            context['popular_tags'] = []
        
        context['featured_posts'] = BlogPost.objects.filter(
            status='published',
            is_featured=True
        ).order_by('-published_at')[:3]
        return context


class PostDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_object(self):
        post = get_object_or_404(
            BlogPost,
            slug=self.kwargs['slug'],
            status='published'
        )
        
        # Track page view
        self.track_view(post)
        
        return post
    
    def track_view(self, post):
        # Update post view count
        BlogPost.objects.filter(id=post.id).update(views_count=F('views_count') + 1)
        
        # Track in analytics
        PageView.objects.create(
            page_type='blog_post',
            page_title=post.title,
            url=self.request.build_absolute_uri(),
            blog_post=post,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            referrer=self.request.META.get('HTTP_REFERER', ''),
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=self.request.session.session_key or ''
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Related posts
        context['related_posts'] = post.get_related_posts()
        
        # Comments
        context['comments'] = post.comments.filter(
            is_approved=True,
            parent__isnull=True
        ).order_by('created_at')
        
        # Rating info
        context['average_rating'] = post.get_average_rating()
        context['rating_count'] = post.get_rating_count()
        
        # Previous/Next posts
        context['previous_post'] = post.get_previous_post()
        context['next_post'] = post.get_next_post()
        
        return context


class CategoryDetailView(ListView):
    model = BlogPost
    template_name = 'blog/category_detail.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return BlogPost.objects.filter(
            category=self.category,
            status='published'
        ).order_by('-published_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        # Add categories for the template
        context['categories'] = Category.objects.filter(is_active=True).order_by('order')
        return context


class TagDetailView(ListView):
    model = BlogPost
    template_name = 'blog/tag_detail.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return BlogPost.objects.filter(
            tags=self.tag,
            status='published'
        ).order_by('-published_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        # Add popular tags for the template
        try:
            from django.db.models import Count
            context['popular_tags'] = Tag.objects.annotate(
                num_times=Count('taggit_taggeditem')
            ).order_by('-num_times')[:10]
        except Exception:
            context['popular_tags'] = []
        return context


class SearchView(ListView):
    model = BlogPost
    template_name = 'blog/search_results.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return BlogPost.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(tags__name__icontains=query),
                status='published'
            ).distinct().order_by('-published_at')
        return BlogPost.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class RatePostView(View):
    def post(self, request, post_id):
        post = get_object_or_404(BlogPost, id=post_id, status='published')
        stars = request.POST.get('stars')
        
        if not stars or not stars.isdigit() or int(stars) not in range(1, 6):
            return JsonResponse({'error': 'Invalid rating'}, status=400)
        
        # Use IP address as user identifier for anonymous users
        user_identifier = self.get_client_ip(request)
        
        # Check if user already rated this post
        rating, created = Rating.objects.get_or_create(
            post=post,
            user_identifier=user_identifier,
            defaults={
                'stars': int(stars),
                'ip_address': user_identifier,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )
        
        if not created:
            # Update existing rating
            rating.stars = int(stars)
            rating.save()
            message = 'Rating updated successfully!'
        else:
            message = 'Thank you for rating this post!'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'average_rating': post.get_average_rating(),
            'rating_count': post.get_rating_count()
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CreatePostView(LoginRequiredMixin, CreateView):
    model = BlogPost
    template_name = 'blog/create_post.html'
    fields = ['title', 'excerpt', 'content', 'featured_image', 'category', 'status', 'is_featured']
    success_url = reverse_lazy('blog:post_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Only staff members can create posts.')
            return redirect('blog:post_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        
        # Handle the action parameter from the button clicked
        action = self.request.POST.get('action', '')
        
        if action == 'publish':
            # When "Publish Post" button is clicked
            form.instance.status = 'published'
            form.instance.published_at = timezone.now()
            success_message = f'Post "{form.instance.title}" published successfully!'
        elif action == 'save_draft':
            # When "Save as Draft" button is clicked
            form.instance.status = 'draft'
            form.instance.published_at = None
            success_message = f'Post "{form.instance.title}" saved as draft successfully!'
        else:
            # Default behavior - use the status from the form
            if form.instance.status == 'published':
                form.instance.published_at = timezone.now()
            success_message = f'Post "{form.instance.title}" created successfully!'
        
        # Save the form first to generate the slug
        response = super().form_valid(form)
        
        # Handle tags after the post is saved
        tags = self.request.POST.get('tags', '')
        if tags:
            self.object.tags.add(*[tag.strip() for tag in tags.split(',') if tag.strip()])
        
        messages.success(self.request, success_message)
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ensure all essential categories exist
        ensure_essential_categories()
        
        # Get all active categories (including newly created ones)
        categories = Category.objects.filter(is_active=True).order_by('order')
        
        context['categories'] = categories
        return context


class EditPostView(LoginRequiredMixin, UpdateView):
    model = BlogPost
    template_name = 'blog/edit_post.html'
    fields = ['title', 'excerpt', 'content', 'featured_image', 'category', 'status', 'is_featured']
    success_url = reverse_lazy('blog:admin_post_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Only staff members can edit posts.')
            return redirect('blog:post_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Handle tags
        tags = self.request.POST.get('tags', '')
        if tags:
            form.instance.save()
            form.instance.tags.clear()
            form.instance.tags.add(*[tag.strip() for tag in tags.split(',') if tag.strip()])
        
        messages.success(self.request, 'Post updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ensure all essential categories exist
        ensure_essential_categories()
        
        # Get all active categories (including newly created ones)
        categories = Category.objects.filter(is_active=True).order_by('order')
        
        context['categories'] = categories
        return context


class AddCommentView(View):
    def post(self, request, post_id):
        post = get_object_or_404(BlogPost, id=post_id, status='published')
        
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        if not all([name, email, content]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('blog:post_detail', slug=post.slug)
        
        # Create comment
        comment = Comment.objects.create(
            post=post,
            name=name,
            email=email,
            content=content,
            parent_id=parent_id if parent_id else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_approved=True  # Auto-approve for now, can be changed later
        )
        
        messages.success(request, 'Your comment has been added successfully!')
        return redirect('blog:post_detail', slug=post.slug)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminPostListView(LoginRequiredMixin, ListView):
    model = BlogPost
    template_name = 'blog/admin_post_list.html'
    context_object_name = 'posts'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('blog:post_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return BlogPost.objects.all().select_related('author', 'category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_posts'] = BlogPost.objects.count()
        context['published_posts'] = BlogPost.objects.filter(status='published').count()
        context['draft_posts'] = BlogPost.objects.filter(status='draft').count()
        return context


class AdminCommentListView(LoginRequiredMixin, ListView):
    model = Comment
    template_name = 'blog/admin_comment_list.html'
    context_object_name = 'comments'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('blog:post_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Comment.objects.all().select_related('post', 'parent').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_comments'] = Comment.objects.count()
        context['pending_comments'] = Comment.objects.filter(is_approved=False).count()
        context['approved_comments'] = Comment.objects.filter(is_approved=True).count()
        return context


class AdminDeletePostView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('blog:post_list')
        
        post = get_object_or_404(BlogPost, id=post_id)
        post_title = post.title
        post.delete()
        messages.success(request, f'Post "{post_title}" has been deleted successfully.')
        return redirect('blog:admin_post_list')


class AdminDeleteCommentView(LoginRequiredMixin, View):
    def post(self, request, comment_id):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('blog:post_list')
        
        comment = get_object_or_404(Comment, id=comment_id)
        comment_content = comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
        comment.delete()
        messages.success(request, f'Comment "{comment_content}" has been deleted successfully.')
        return redirect('blog:admin_comment_list')


class AdminApproveCommentView(LoginRequiredMixin, View):
    def post(self, request, comment_id):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('blog:post_list')
        
        comment = get_object_or_404(Comment, id=comment_id)
        comment.is_approved = True
        comment.save()
        messages.success(request, 'Comment has been approved successfully.')
        return redirect('blog:admin_comment_list')


class AdminPostStatsView(LoginRequiredMixin, TemplateView):
    template_name = 'blog/admin_post_stats.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('blog:post_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Post statistics
        context['total_posts'] = BlogPost.objects.count()
        context['published_posts'] = BlogPost.objects.filter(status='published').count()
        context['draft_posts'] = BlogPost.objects.filter(status='draft').count()
        context['featured_posts'] = BlogPost.objects.filter(is_featured=True).count()
        
        # Rating statistics
        from django.db.models import Avg
        context['avg_rating'] = Rating.objects.aggregate(avg=Avg('stars'))['avg'] or 0
        context['total_ratings'] = Rating.objects.count()
        
        # View statistics
        context['total_views'] = BlogPost.objects.aggregate(total=Sum('views_count'))['total'] or 0
        
        # Recent activity
        context['recent_posts'] = BlogPost.objects.order_by('-created_at')[:10]
        context['recent_comments'] = Comment.objects.order_by('-created_at')[:10]
        
        return context