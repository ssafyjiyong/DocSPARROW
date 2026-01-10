from django.contrib import admin
from .models import Country, Product, ProductVersion, Category, Artifact


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'flag_emoji', 'display_order']
    list_editable = ['display_order']
    search_fields = ['name', 'code']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_class', 'display_order']
    list_editable = ['display_order']
    search_fields = ['name']


@admin.register(ProductVersion)
class ProductVersionAdmin(admin.ModelAdmin):
    list_display = ['product', 'version_number', 'is_active', 'created_at']
    list_filter = ['product', 'is_active']
    search_fields = ['version_number', 'product__name']
    list_editable = ['is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order']
    list_editable = ['display_order']
    search_fields = ['name']


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ['country', 'product', 'category', 'version_string', 'uploader', 'created_at', 'filename']
    list_filter = ['country', 'product', 'category', 'created_at']
    search_fields = ['version_string', 'product__name', 'category__name']
    readonly_fields = ['created_at']
    
    def filename(self, obj):
        return obj.filename
    filename.short_description = '파일명'
