from django.core.management.base import BaseCommand
from articles.models import Category


class Command(BaseCommand):
    help = 'Seed the database with initial categories'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'Latest', 'slug': 'latest', 'description': 'Breaking and latest news', 'order': 1},
            {'name': 'Politics', 'slug': 'politics', 'description': 'Political news and analysis', 'order': 2},
            {'name': 'Crime', 'slug': 'crime', 'description': 'Crime reports and investigations', 'order': 3},
            {'name': 'Opinion', 'slug': 'opinion', 'description': 'Editorial opinions and columns', 'order': 4},
            {'name': 'Business', 'slug': 'business', 'description': 'Business and financial news', 'order': 5},
            {'name': 'Sports', 'slug': 'sports', 'description': 'Sports news and updates', 'order': 6},
            {'name': 'Entertainment', 'slug': 'entertainment', 'description': 'Entertainment and celebrity news', 'order': 7},
            {'name': 'Jobs', 'slug': 'jobs', 'description': 'Career and employment news', 'order': 8},
            {'name': 'Tech', 'slug': 'tech', 'description': 'Technology news and reviews', 'order': 9},
        ]

        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))

        self.stdout.write(self.style.SUCCESS('Category seeding completed!'))