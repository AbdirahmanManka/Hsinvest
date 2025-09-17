from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.db.models import Count
from .models import PageView

class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Time range: last 30 days
        today = timezone.now().date()
        start_date = today - timedelta(days=29)

        # Aggregate daily total views and unique visitors
        views_qs = PageView.objects.filter(viewed_at__date__gte=start_date)

        daily_views = (
            views_qs
            .annotate(day=TruncDate('viewed_at'))
            .values('day')
            .annotate(total=Count('id'))
            .order_by('day')
        )

        # Unique visitors per day using distinct IPs
        unique_per_day = (
            views_qs
            .annotate(day=TruncDate('viewed_at'))
            .values('day', 'ip_address')
            .distinct()
            .values('day')
            .annotate(total=Count('day'))
            .order_by('day')
        )

        # Build aligned series for Chart.js
        labels = []
        views_series = []
        unique_series = []

        # Build lookup dicts
        views_map = {item['day']: item['total'] for item in daily_views}
        unique_map = {item['day']: item['total'] for item in unique_per_day}

        for i in range(30):
            day = start_date + timedelta(days=i)
            labels.append(day.strftime('%b %d'))
            views_series.append(views_map.get(day, 0))
            unique_series.append(unique_map.get(day, 0))

        context.update({
            'labels': labels,
            'views_series': views_series,
            'unique_series': unique_series,
            'start_date': start_date,
            'end_date': today,
        })

        return context