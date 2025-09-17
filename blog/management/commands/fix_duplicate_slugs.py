from django.core.management.base import BaseCommand
from django.db import models
from blog.models import BlogPost
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Fix duplicate slugs in BlogPost model'

    def handle(self, *args, **options):
        # Find posts with duplicate slugs
        duplicates = BlogPost.objects.values('slug').annotate(
            count=models.Count('slug')
        ).filter(count__gt=1)
        
        if not duplicates:
            self.stdout.write(
                self.style.SUCCESS('No duplicate slugs found!')
            )
            return
        
        self.stdout.write(f'Found {len(duplicates)} duplicate slugs')
        
        for duplicate in duplicates:
            slug = duplicate['slug']
            posts = BlogPost.objects.filter(slug=slug).order_by('created_at')
            
            self.stdout.write(f'Fixing slug: {slug}')
            
            # Keep the first post with the original slug
            first_post = posts.first()
            self.stdout.write(f'  Keeping original slug for: {first_post.title}')
            
            # Update the rest with unique slugs
            for i, post in enumerate(posts[1:], 1):
                base_slug = slugify(post.title)
                new_slug = f"{base_slug}-{i}"
                
                # Make sure the new slug is unique
                counter = 1
                while BlogPost.objects.filter(slug=new_slug).exists():
                    new_slug = f"{base_slug}-{i}-{counter}"
                    counter += 1
                
                post.slug = new_slug
                post.save()
                self.stdout.write(f'  Updated: {post.title} -> {new_slug}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully fixed all duplicate slugs!')
        )

