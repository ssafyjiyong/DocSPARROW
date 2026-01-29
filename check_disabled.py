import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docsparrow.settings')
django.setup()

from artifacts.models import ProductCategoryDisabled, Country

# Check all disabled cells
all_disabled = ProductCategoryDisabled.objects.all()
print(f"Total disabled cells: {all_disabled.count()}")
for d in all_disabled:
    print(f"  [{d.country.code}] {d.product.name} - {d.category.name}")

# Check KR disabled cells
kr = Country.objects.get(code='KR')
kr_disabled = ProductCategoryDisabled.objects.filter(country=kr)
print(f"\nKR disabled cells: {kr_disabled.count()}")

# Check US disabled cells  
us = Country.objects.get(code='US')
us_disabled = ProductCategoryDisabled.objects.filter(country=us)
print(f"US disabled cells: {us_disabled.count()}")
