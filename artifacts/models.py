from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models


class Country(models.Model):
    """국가 모델 (4개 국가)"""
    code = models.CharField(max_length=10, unique=True, verbose_name="국가 코드")
    name = models.CharField(max_length=100, verbose_name="국가명")
    flag_emoji = models.CharField(max_length=10, verbose_name="국기 이모지", default="🌐")
    flag_icon = models.CharField(max_length=100, verbose_name="국기 아이콘", blank=True, help_text="예: free-icon-flag-KR.png")
    display_order = models.IntegerField(default=0, verbose_name="정렬 순서")

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "국가"
        verbose_name_plural = "국가"

    def __str__(self):
        return f"{self.flag_emoji} {self.name}"


class Product(models.Model):
    """제품 모델 (10개 제품)"""
    name = models.CharField(max_length=100, verbose_name="제품명")
    color_class = models.CharField(max_length=50, verbose_name="Tailwind 색상 클래스", 
                                   help_text="예: bg-green-500")
    display_order = models.IntegerField(default=0, verbose_name="정렬 순서")

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "제품"
        verbose_name_plural = "제품"

    def __str__(self):
        return self.name


class ProductVersion(models.Model):
    """제품 버전 모델"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                               related_name='versions', verbose_name="제품")
    version_number = models.CharField(max_length=50, verbose_name="버전 번호", 
                                     help_text="예: 2512.2")
    is_active = models.BooleanField(default=False, verbose_name="기본 버전")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "제품 버전"
        verbose_name_plural = "제품 버전"

    def __str__(self):
        return f"{self.product.name} {self.version_number}"

    def save(self, *args, **kwargs):
        # 기본 버전으로 설정되면 같은 제품의 다른 버전은 기본에서 해제
        if self.is_active:
            ProductVersion.objects.filter(product=self.product).update(is_active=False)
        super().save(*args, **kwargs)


class Category(models.Model):
    """문서 카테고리 모델 (17개 카테고리)"""
    DEPARTMENT_CHOICES = [
        ('consulting', '컨설팅'),
        ('business', '사업'),
        ('marketing', '마케팅'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="카테고리명")
    department = models.CharField(
        max_length=20, 
        choices=DEPARTMENT_CHOICES, 
        verbose_name="담당 부서",
        default='consulting'
    )
    display_order = models.IntegerField(default=0, verbose_name="정렬 순서")

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "카테고리"
        verbose_name_plural = "카테고리"

    def __str__(self):
        return self.name


class Artifact(models.Model):
    """산출물 모델"""
    country = models.ForeignKey(Country, on_delete=models.CASCADE,
                               related_name='artifacts', verbose_name="국가",
                               null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                               related_name='artifacts', verbose_name="제품")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, 
                                related_name='artifacts', verbose_name="카테고리")
    file = models.FileField(upload_to='artifacts/%Y/%m/', verbose_name="파일")
    version_string = models.CharField(max_length=50, verbose_name="산출물 버전", 
                                     help_text="예: 5.18.0")
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                verbose_name="업로드한 사용자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록일")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "산출물"
        verbose_name_plural = "산출물"
        indexes = [
            models.Index(fields=['country', 'product', 'category', '-created_at']),
        ]

    def __str__(self):
        country_str = self.country.code if self.country else "Global"
        return f"[{country_str}] {self.product.name} - {self.category.name} (v{self.version_string})"

    @property
    def filename(self):
        """파일명 반환"""
        import os
        return os.path.basename(self.file.name)


class ProductCategoryDisabled(models.Model):
    """제품-카테고리 비활성화 (해당 없음 표시) - 국가별"""
    country = models.ForeignKey(Country, on_delete=models.CASCADE,
                               related_name='disabled_cells', verbose_name="국가")
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                               related_name='disabled_categories', verbose_name="제품")
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                related_name='disabled_products', verbose_name="카테고리")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="비활성화 일시")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  verbose_name="비활성화한 관리자")

    class Meta:
        verbose_name = "비활성화된 셀"
        verbose_name_plural = "비활성화된 셀"
        unique_together = [['country', 'product', 'category']]
        indexes = [
            models.Index(fields=['country', 'product', 'category']),
        ]

    def __str__(self):
        return f"[{self.country.code}] {self.product.name} - {self.category.name} (비활성화)"


