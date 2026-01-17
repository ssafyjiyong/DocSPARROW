from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from artifacts.models import Product, Artifact, Category, Country
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Create test data for DocSPARROW'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...\n')

        # Get or create users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('Test123!@')
        admin_user.save()

        jeffrey_user, _ = User.objects.get_or_create(
            username='jeffreykim',
            defaults={'is_staff': False}
        )
        jeffrey_user.set_password('a1234567!')
        jeffrey_user.save()

        # Create another test user
        test_user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={'is_staff': False}
        )
        test_user.set_password('test1234!')
        test_user.save()

        self.stdout.write(self.style.SUCCESS('✓ Users: admin, jeffreykim, testuser'))

        # Get or create countries
        country_data = [
            ('KR', '한국', '🇰🇷'),
            ('US', '미국', '🇺🇸'),
            ('JP', '일본', '🇯🇵'),
            ('CN', '중국', '🇨🇳'),
        ]
        
        countries = []
        for code, name, emoji in country_data:
            country, _ = Country.objects.get_or_create(
                code=code,
                defaults={'name': name, 'flag_emoji': emoji}
            )
            countries.append(country)

        # Get or create products
        products = []
        product_data = [
            ('Enterprise Solution', 'bg-blue-500'),
            ('Standard Package', 'bg-green-500'),
            ('Premium Service', 'bg-purple-500'),
        ]
        
        for idx, (name, color) in enumerate(product_data):
            product, _ = Product.objects.get_or_create(
                name=name,
                defaults={'color_class': color, 'display_order': idx}
            )
            products.append(product)
            self.stdout.write(f'✓ Product: {name}')

        # Get or create categories
        category_names = [
            '제품소개서',
            '사용자매뉴얼',
            '기술문서',
            '릴리즈노트',
        ]
        
        categories = []
        for idx, cat_name in enumerate(category_names):
            category, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={'display_order': idx}
            )
            categories.append(category)

        # Create artifacts
        self.stdout.write('\nCreating artifacts...')
        versions = ['1.0.0', '1.1.0', '1.2.0', '2.0.0', '2.1.0', '3.0.0']
        artifact_count = 0

        for product in products:
            for category in categories:
                # Create 3-5 artifacts for each product-category combination
                num_artifacts = random.randint(3, 5)
                
                for i in range(num_artifacts):
                    version = random.choice(versions)
                    country = random.choice(countries + [None])  # Some without country
                    
                    # Randomly assign uploader (more from jeffrey, some from test_user, some from admin)
                    uploader = random.choices(
                        [jeffrey_user, test_user, admin_user],
                        weights=[5, 3, 2]
                    )[0]
                    
                    country_code = country.code if country else 'Global'
                    filename = f"{product.name}_{category.name}_{version}_{country_code}.pdf"
                    
                    # Create artifact with dummy file
                    artifact = Artifact()
                    artifact.product = product
                    artifact.category = category
                    artifact.country = country
                    artifact.version_string = version
                    artifact.uploader = uploader
                    
                    # Create dummy file
                    dummy_content = f"Dummy PDF content for {filename}".encode('utf-8')
                    artifact.file.save(filename, ContentFile(dummy_content), save=False)
                    
                    artifact.save()
                    artifact_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {artifact_count} artifacts'))

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write('SUMMARY')
        self.stdout.write('='*60)
        for product in products:
            artifacts_count = Artifact.objects.filter(product=product).count()
            versions_count = Artifact.objects.filter(product=product).values('version_string').distinct().count()
            self.stdout.write(f'{product.name:20} - {artifacts_count:2} artifacts, {versions_count} versions')

        self.stdout.write('\nArtifacts by uploader:')
        for user in [admin_user, jeffrey_user, test_user]:
            count = Artifact.objects.filter(uploader=user).count()
            self.stdout.write(f'  {user.username:12} - {count} artifacts')

        self.stdout.write(self.style.SUCCESS('\n✓ Test data creation complete!'))
