from django.core.management.base import BaseCommand
from artifacts.models import Product, ProductVersion


class Command(BaseCommand):
    help = '각 제품에 테스트용 버전을 추가합니다.'

    def handle(self, *args, **options):
        self.stdout.write('제품 버전을 생성합니다...')

        products = Product.objects.all()
        
        # 각 제품에 2-3개 버전 추가
        version_sets = [
            ["2512.1", "2512.2", "2601.0"],  # 기본 버전 패턴
        ]
        
        for product in products:
            for i, version_num in enumerate(version_sets[0]):
                version, created = ProductVersion.objects.get_or_create(
                    product=product,
                    version_number=version_num,
                    defaults={'is_active': i == 1}  # 두 번째 버전을 기본으로 설정
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'{product.name} v{version_num} 생성 (기본: {version.is_active})'
                    ))
                else:
                    self.stdout.write(f'{product.name} v{version_num} 이미 존재')

        self.stdout.write(self.style.SUCCESS('제품 버전 생성이 완료되었습니다!'))
