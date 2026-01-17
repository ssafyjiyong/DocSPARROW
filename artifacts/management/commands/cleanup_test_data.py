from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from artifacts.models import Product, Artifact, Category, Country


class Command(BaseCommand):
    help = 'Clean up test data from DocSPARROW'

    def handle(self, *args, **options):
        self.stdout.write('Deleting test data...\n')

        # Delete test users
        test_usernames = ['testuser']
        deleted_users = User.objects.filter(username__in=test_usernames).delete()
        self.stdout.write(f'✓ Deleted {deleted_users[0]} test users')

        # Delete test products (created during test)
        test_products = ['Enterprise Solution', 'Standard Package', 'Premium Service']
        deleted_products = Product.objects.filter(name__in=test_products).delete()
        self.stdout.write(f'✓ Deleted {deleted_products[0]} test products (and related artifacts)')

        # Delete GL country if it exists
        gl_country = Country.objects.filter(code='GL').delete()
        if gl_country[0] > 0:
            self.stdout.write(f'✓ Deleted GL country (and {gl_country[0]} related items)')
        else:
            self.stdout.write('✓ GL country not found (already clean)')

        # Check remaining data
        self.stdout.write('\n' + '='*60)
        self.stdout.write('REMAINING DATA')
        self.stdout.write('='*60)
        
        users_count = User.objects.count()
        products_count = Product.objects.count()
        artifacts_count = Artifact.objects.count()
        countries_count = Country.objects.count()
        
        self.stdout.write(f'Users: {users_count}')
        self.stdout.write(f'Products: {products_count}')
        self.stdout.write(f'Artifacts: {artifacts_count}')
        self.stdout.write(f'Countries: {countries_count}')

        self.stdout.write(self.style.SUCCESS('\n✓ Test data cleanup complete!'))
