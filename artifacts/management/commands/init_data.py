from django.core.management.base import BaseCommand
from artifacts.models import Country, Product, Category


class Command(BaseCommand):
    help = '4개 국가, 10개 제품, 17개 카테고리를 자동 생성합니다.'

    def handle(self, *args, **options):
        self.stdout.write('초기 데이터를 생성합니다...')

        # 4개 국가 생성
        countries_data = [
            {"code": "KR", "name": "한국", "flag_emoji": "🇰🇷", "flag_icon": "free-icon-flag-KR.png", "display_order": 1},
            {"code": "US", "name": "미국", "flag_emoji": "🇺🇸", "flag_icon": "free-icon-flag-US.png", "display_order": 2},
            {"code": "JP", "name": "일본", "flag_emoji": "🇯🇵", "flag_icon": "free-icon-flag-JP.png", "display_order": 3},
            {"code": "ES", "name": "스페인", "flag_emoji": "🇪🇸", "flag_icon": "free-icon-flag-ES.png", "display_order": 4},
        ]

        for country_data in countries_data:
            country, created = Country.objects.get_or_create(
                code=country_data["code"],
                defaults={
                    "name": country_data["name"],
                    "flag_emoji": country_data["flag_emoji"],
                    "flag_icon": country_data["flag_icon"],
                    "display_order": country_data["display_order"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'국가 생성: {country.name}'))
            else:
                # 기존 국가의 flag_icon 업데이트
                if not country.flag_icon:
                    country.flag_icon = country_data["flag_icon"]
                    country.save()
                    self.stdout.write(self.style.SUCCESS(f'국가 아이콘 업데이트: {country.name}'))
                else:
                    self.stdout.write(f'국가 이미 존재: {country.name}')

        # 10개 제품 생성
        products_data = [
            {"name": "Enterprise", "color_class": "bg-green-500", "display_order": 1},
            {"name": "SAST", "color_class": "bg-red-500", "display_order": 2},
            {"name": "SAQT", "color_class": "bg-indigo-600", "display_order": 3},
            {"name": "DAST", "color_class": "bg-orange-500", "display_order": 4},
            {"name": "SCA", "color_class": "bg-yellow-500", "display_order": 5},
            {"name": "P-Cloud", "color_class": "bg-blue-500", "display_order": 6},
            {"name": "G-Cloud", "color_class": "bg-green-600", "display_order": 7},
            {"name": "SecureHub", "color_class": "bg-blue-600", "display_order": 8},
            {"name": "On-Demand", "color_class": "bg-teal-500", "display_order": 9},
            {"name": "MCP", "color_class": "bg-purple-500", "display_order": 10},
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data["name"],
                defaults={
                    "color_class": product_data["color_class"],
                    "display_order": product_data["display_order"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'제품 생성: {product.name}'))
            else:
                self.stdout.write(f'제품 이미 존재: {product.name}')

        # 17개 카테고리 생성
        categories_data = [
            {"name": "제품소개서", "display_order": 1},
            {"name": "브로슈어", "display_order": 2},
            {"name": "사례집(Use-CASE)", "display_order": 3},
            {"name": "제품비교표", "display_order": 4},
            {"name": "기능비교자료", "display_order": 5},
            {"name": "BM비교자료", "display_order": 6},
            {"name": "시장점유율", "display_order": 7},
            {"name": "설치가이드", "display_order": 8},
            {"name": "사용설명서", "display_order": 9},
            {"name": "사용가이드", "display_order": 10},
            {"name": "관리자가이드", "display_order": 11},
            {"name": "규격서", "display_order": 12},
            {"name": "릴리즈노트", "display_order": 13},
            {"name": "사업계획서", "display_order": 14},
            {"name": "컴플라이언스/가이드", "display_order": 15},
            {"name": "인증서", "display_order": 16},
            {"name": "특허정보", "display_order": 17},
        ]

        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=category_data["name"],
                defaults={"display_order": category_data["display_order"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'카테고리 생성: {category.name}'))
            else:
                self.stdout.write(f'카테고리 이미 존재: {category.name}')

        self.stdout.write(self.style.SUCCESS('초기 데이터 생성이 완료되었습니다!'))
