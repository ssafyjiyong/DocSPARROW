from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Category, Product
import json


def is_staff_user(user):
    """Check if user is staff/admin"""
    return user.is_staff


@login_required
@user_passes_test(is_staff_user)
def admin_management(request):
    """Admin management page for categories and products"""
    categories = Category.objects.all()
    products = Product.objects.all()
    
    context = {
        'categories': categories,
        'products': products,
    }
    
    return render(request, 'artifacts/admin_manage.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def category_create(request):
    """Create a new category"""
    try:
        name = request.POST.get('name', '').strip()
        display_order = request.POST.get('display_order', 0)
        
        if not name:
            return JsonResponse({'success': False, 'error': '카테고리명을 입력해주세요.'}, status=400)
        
        # Check if category with same name exists
        if Category.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': '이미 존재하는 카테고리명입니다.'}, status=400)
        
        category = Category.objects.create(
            name=name,
            display_order=int(display_order)
        )
        
        return JsonResponse({
            'success': True,
            'message': '카테고리가 생성되었습니다.',
            'category': {
                'id': category.id,
                'name': category.name,
                'display_order': category.display_order
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def category_update(request, category_id):
    """Update an existing category"""
    try:
        category = get_object_or_404(Category, id=category_id)
        name = request.POST.get('name', '').strip()
        display_order = request.POST.get('display_order', 0)
        
        if not name:
            return JsonResponse({'success': False, 'error': '카테고리명을 입력해주세요.'}, status=400)
        
        # Check if another category with same name exists
        if Category.objects.filter(name=name).exclude(id=category_id).exists():
            return JsonResponse({'success': False, 'error': '이미 존재하는 카테고리명입니다.'}, status=400)
        
        category.name = name
        category.display_order = int(display_order)
        category.save()
        
        return JsonResponse({
            'success': True,
            'message': '카테고리가 수정되었습니다.',
            'category': {
                'id': category.id,
                'name': category.name,
                'display_order': category.display_order
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def category_delete(request, category_id):
    """Delete a category"""
    try:
        category = get_object_or_404(Category, id=category_id)
        
        # Check if category has artifacts
        if category.artifacts.exists():
            return JsonResponse({
                'success': False,
                'error': '이 카테고리에 연결된 산출물이 있어 삭제할 수 없습니다.'
            }, status=400)
        
        category_name = category.name
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'"{category_name}" 카테고리가 삭제되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def product_create(request):
    """Create a new product"""
    try:
        name = request.POST.get('name', '').strip()
        color_class = request.POST.get('color_class', '').strip()
        display_order = request.POST.get('display_order', 0)
        
        if not name:
            return JsonResponse({'success': False, 'error': '제품명을 입력해주세요.'}, status=400)
        
        if not color_class:
            return JsonResponse({'success': False, 'error': '색상을 선택해주세요.'}, status=400)
        
        # Check if product with same name exists
        if Product.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': '이미 존재하는 제품명입니다.'}, status=400)
        
        product = Product.objects.create(
            name=name,
            color_class=color_class,
            display_order=int(display_order)
        )
        
        return JsonResponse({
            'success': True,
            'message': '제품이 생성되었습니다.',
            'product': {
                'id': product.id,
                'name': product.name,
                'color_class': product.color_class,
                'display_order': product.display_order
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def product_update(request, product_id):
    """Update an existing product"""
    try:
        product = get_object_or_404(Product, id=product_id)
        name = request.POST.get('name', '').strip()
        color_class = request.POST.get('color_class', '').strip()
        display_order = request.POST.get('display_order', 0)
        
        if not name:
            return JsonResponse({'success': False, 'error': '제품명을 입력해주세요.'}, status=400)
        
        if not color_class:
            return JsonResponse({'success': False, 'error': '색상을 선택해주세요.'}, status=400)
        
        # Check if another product with same name exists
        if Product.objects.filter(name=name).exclude(id=product_id).exists():
            return JsonResponse({'success': False, 'error': '이미 존재하는 제품명입니다.'}, status=400)
        
        product.name = name
        product.color_class = color_class
        product.display_order = int(display_order)
        product.save()
        
        return JsonResponse({
            'success': True,
            'message': '제품이 수정되었습니다.',
            'product': {
                'id': product.id,
                'name': product.name,
                'color_class': product.color_class,
                'display_order': product.display_order
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def product_delete(request, product_id):
    """Delete a product"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Check if product has artifacts
        if product.artifacts.exists():
            return JsonResponse({
                'success': False,
                'error': '이 제품에 연결된 산출물이 있어 삭제할 수 없습니다.'
            }, status=400)
        
        product_name = product.name
        product.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'"{product_name}" 제품이 삭제되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
