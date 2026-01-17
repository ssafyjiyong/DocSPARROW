import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DocSPARROW.settings')
django.setup()

from django.contrib.auth.models import User
from artifacts.models import Product, Artifact

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

print(f"✓ Users created/updated: admin, jeffreykim, testuser")

# Get or create products
products = []
product_names = {
    'Enterprise': '엔터프라이즈 솔루션',
    'Standard': '표준 패키지',
    'Premium': '프리미엄 서비스'
}

for code, name in product_names.items():
    product, created = Product.objects.get_or_create(
        code=code,
        defaults={'name': name}
    )
    products.append(product)
    print(f"✓ Product: {code} - {name}")

# Artifact types
artifact_types = [
    ('제품소개서', 'product_intro'),
    ('사용자매뉴얼', 'user_manual'),
    ('기술문서', 'tech_doc'),
    ('릴리즈노트', 'release_note')
]

countries = ['KR', 'US', 'JP', 'CN', 'UK', 'DE']
versions = ['1.0.0', '1.1.0', '1.2.0', '2.0.0', '2.1.0']

# Create artifacts
print("\nCreating artifacts...")
artifact_count = 0

for product in products:
    for artifact_type_kr, artifact_type_code in artifact_types:
        # Create 3-5 versions for each artifact type
        num_versions = random.randint(3, 5)
        
        for i in range(num_versions):
            version = random.choice(versions)
            country = random.choice(countries)
            
            # Randomly assign uploader (more from jeffrey, some from test_user, some from admin)
            uploader = random.choices(
                [jeffrey_user, test_user, admin_user],
                weights=[5, 3, 2]
            )[0]
            
            # Create artifact
            artifact = Artifact.objects.create(
                product=product,
                artifact_type=artifact_type_kr,
                country=country,
                version=version,
                file_name=f"{product.code}_{artifact_type_code}_{version}_{country}.pdf",
                file_path=f"/dummy/path/{product.code}/{artifact_type_code}/{version}/{country}.pdf",
                file_size=random.randint(100000, 5000000),
                uploader=uploader,
                created_at=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            artifact_count += 1

print(f"\n✓ Created {artifact_count} artifacts")

# Print summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for product in products:
    artifacts_count = Artifact.objects.filter(product=product).count()
    versions_count = Artifact.objects.filter(product=product).values('version').distinct().count()
    print(f"{product.code:12} - {artifacts_count:2} artifacts, {versions_count} versions")

print("\nArtifacts by uploader:")
for user in [admin_user, jeffrey_user, test_user]:
    count = Artifact.objects.filter(uploader=user).count()
    print(f"  {user.username:12} - {count} artifacts")

print("\n✓ Test data creation complete!")
