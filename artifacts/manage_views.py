from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Category, Product, ProductCategoryDisabled
import json


def is_staff_user(user):
    """Check if user is staff/admin"""
    return user.is_staff


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_superuser



@login_required
@user_passes_test(is_staff_user)
def admin_management(request):
    """Admin management page for categories and products"""
    from .models import Country
    
    categories = Category.objects.all()
    products = Product.objects.all()
    countries = Country.objects.all()
    
    # Get current selected country (default to first country, typically KR)
    selected_country_id = request.GET.get('country_id')
    if selected_country_id:
        selected_country = get_object_or_404(Country, id=selected_country_id)
    else:
        selected_country = countries.first()
    
    # Get disabled cells for the selected country
    disabled_cells = ProductCategoryDisabled.objects.filter(
        country=selected_country
    ).select_related('product', 'category')
    # Convert to list of lists for JavaScript compatibility
    disabled_set = [[dc.product.id, dc.category.id] for dc in disabled_cells]
    
    context = {
        'categories': categories,
        'products': products,
        'countries': countries,
        'selected_country': selected_country,
        'disabled_set': disabled_set,
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


@login_required
@user_passes_test(is_staff_user)
def get_disabled_cells(request):
    """Get all disabled product-category combinations for a specific country"""
    from .models import Country
    
    country_id = request.GET.get('country_id')
    if not country_id:
        return JsonResponse({'success': False, 'error': 'country_id가 필요합니다.'}, status=400)
    
    country = get_object_or_404(Country, id=country_id)
    disabled_cells = ProductCategoryDisabled.objects.filter(
        country=country
    ).select_related('product', 'category')
    
    disabled_list = [{
        'product_id': cell.product.id,
        'category_id': cell.category.id,
        'product_name': cell.product.name,
        'category_name': cell.category.name,
    } for cell in disabled_cells]
    
    return JsonResponse({'disabled_cells': disabled_list})


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def toggle_disabled_cell(request):
    """Toggle disabled status for a product-category combination for a specific country"""
    from .models import Country
    
    try:
        product_id = request.POST.get('product_id')
        category_id = request.POST.get('category_id')
        country_id = request.POST.get('country_id')
        
        if not product_id or not category_id or not country_id:
            return JsonResponse({'success': False, 'error': '제품, 카테고리, 국가를 모두 선택해주세요.'}, status=400)
        
        product = get_object_or_404(Product, id=product_id)
        category = get_object_or_404(Category, id=category_id)
        country = get_object_or_404(Country, id=country_id)
        
        # Check if already disabled for this country
        disabled = ProductCategoryDisabled.objects.filter(
            country=country,
            product=product,
            category=category
        ).first()
        
        if disabled:
            # Enable (remove from disabled list)
            disabled.delete()
            return JsonResponse({
                'success': True,
                'disabled': False,
                'message': f'[{country.code}] {product.name} - {category.name} 셀을 활성화했습니다.'
            })
        else:
            # Disable (add to disabled list)
            ProductCategoryDisabled.objects.create(
                country=country,
                product=product,
                category=category,
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'disabled': True,
                'message': f'[{country.code}] {product.name} - {category.name} 셀을 비활성화했습니다.'
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser)
def login_logs_view(request):
    """로그인 로그 페이지"""
    return render(request, 'artifacts/login_logs.html')


@login_required
@user_passes_test(is_superuser)
def get_login_logs_api(request):
    """로그인 로그 데이터 조회 API"""
    from .models import LoginAttempt
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    try:
        # 필터 파라미터
        success_filter = request.GET.get('success', '')  # 'true', 'false', or ''
        username_search = request.GET.get('username', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        page_number = int(request.GET.get('page', 1))
        
        # 쿼리 시작
        query = LoginAttempt.objects.select_related('user').all()
        
        # 성공/실패 필터
        if success_filter == 'true':
            query = query.filter(success=True)
        elif success_filter == 'false':
            query = query.filter(success=False)
        
        # 사용자명 검색
        if username_search:
            query = query.filter(username__icontains=username_search)
        
        # 날짜 범위 필터
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                # 한국 시간대로 변환
                date_from_aware = timezone.make_aware(date_from_obj)
                query = query.filter(created_at__gte=date_from_aware)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                # 하루의 끝까지 포함
                date_to_obj = date_to_obj + timedelta(days=1)
                date_to_aware = timezone.make_aware(date_to_obj)
                query = query.filter(created_at__lt=date_to_aware)
            except ValueError:
                pass
        
        # 페이지네이션
        paginator = Paginator(query, 50)  # 페이지당 50개
        page_obj = paginator.get_page(page_number)
        
        # 데이터 직렬화
        logs = []
        for attempt in page_obj:
            logs.append({
                'id': attempt.id,
                'username': attempt.username,
                'user_id': attempt.user.id if attempt.user else None,
                'user_fullname': attempt.user.get_full_name() if attempt.user else None,
                'ip_address': attempt.ip_address,
                'user_agent': attempt.user_agent,
                'success': attempt.success,
                'failure_reason': attempt.failure_reason,
                'created_at': timezone.localtime(attempt.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        return JsonResponse({
            'success': True,
            'logs': logs,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser)
def download_logs_view(request):
    """다운로드 로그 페이지"""
    return render(request, 'artifacts/download_logs.html')


@login_required
@user_passes_test(is_superuser)
def get_download_logs_api(request):
    """다운로드 로그 데이터 조회 API"""
    from .models import DownloadLog
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db import models
    
    try:
        # 필터 파라미터
        download_type = request.GET.get('type', '')  # 'single', 'bulk', or ''
        username_search = request.GET.get('username', '').strip()
        product_search = request.GET.get('product', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        page_number = int(request.GET.get('page', 1))
        
        # 쿼리 시작
        query = DownloadLog.objects.select_related(
            'user', 'artifact', 'product', 'country', 'artifact__category', 'artifact__product'
        ).all()
        
        # 다운로드 유형 필터
        if download_type:
            query = query.filter(download_type=download_type)
        
        # 사용자명 검색
        if username_search:
            query = query.filter(user__username__icontains=username_search)
        
        # 제품명 검색
        if product_search:
            query = query.filter(
                models.Q(product__name__icontains=product_search) |
                models.Q(artifact__product__name__icontains=product_search)
            )
        
        # 날짜 범위 필터
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                date_from_aware = timezone.make_aware(date_from_obj)
                query = query.filter(created_at__gte=date_from_aware)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                date_to_obj = date_to_obj + timedelta(days=1)
                date_to_aware = timezone.make_aware(date_to_obj)
                query = query.filter(created_at__lt=date_to_aware)
            except ValueError:
                pass
        
        # 페이지네이션
        paginator = Paginator(query, 50)  # 페이지당 50개
        page_obj = paginator.get_page(page_number)
        
        # 데이터 직렬화
        logs = []
        for log in page_obj:
            log_data = {
                'id': log.id,
                'username': log.user.username if log.user else 'Anonymous',
                'user_id': log.user.id if log.user else None,
                'download_type': log.download_type,
                'download_type_display': log.get_download_type_display(),
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'created_at': timezone.localtime(log.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            if log.download_type == 'single' and log.artifact:
                log_data['artifact'] = {
                    'id': log.artifact.id,
                    'filename': log.artifact.filename,
                    'product_name': log.artifact.product.name,
                    'category_name': log.artifact.category.name,
                    'version': log.artifact.version_string,
                }
            elif log.download_type == 'bulk' and log.product:
                log_data['bulk'] = {
                    'product_name': log.product.name,
                    'country_code': log.country.code if log.country else 'N/A',
                    'artifact_count': log.artifact_count,
                }
            
            logs.append(log_data)
        
        return JsonResponse({
            'success': True,
            'logs': logs,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser)
def unified_logs_view(request):
    """통합 활동 로그 페이지"""
    return render(request, 'artifacts/unified_logs.html')


@login_required
@user_passes_test(is_superuser)
def get_unified_logs_api(request):
    """통합 활동 로그 데이터 조회 API"""
    from .models import LoginAttempt, DownloadLog, ArtifactActivityLog
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import datetime, timedelta
    from itertools import chain
    from operator import attrgetter
    
    try:
        # Filter parameters
        activity_type = request.GET.get('type', '')  # 'login', 'download', 'upload', 'delete', or ''
        username_search = request.GET.get('username', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        page_number = int(request.GET.get('page', 1))
        
        # Collect logs based on activity type filter
        all_logs = []
        
        if not activity_type or activity_type == 'login':
            login_logs = LoginAttempt.objects.all()
            if username_search:
                login_logs = login_logs.filter(username__icontains=username_search)
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    date_from_aware = timezone.make_aware(date_from_obj)
                    login_logs = login_logs.filter(created_at__gte=date_from_aware)
                except ValueError:
                    pass
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    date_to_aware = timezone.make_aware(date_to_obj)
                    login_logs = login_logs.filter(created_at__lt=date_to_aware)
                except ValueError:
                    pass
            all_logs.extend(login_logs)
        
        if not activity_type or activity_type == 'download':
            download_logs = DownloadLog.objects.select_related('user', 'artifact', 'product', 'country').all()
            if username_search:
                download_logs = download_logs.filter(username__icontains=username_search)
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    date_from_aware = timezone.make_aware(date_from_obj)
                    download_logs = download_logs.filter(created_at__gte=date_from_aware)
                except ValueError:
                    pass
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    date_to_aware = timezone.make_aware(date_to_obj)
                    download_logs = download_logs.filter(created_at__lt=date_to_aware)
                except ValueError:
                    pass
            all_logs.extend(download_logs)
        
        if not activity_type or activity_type in ['upload', 'delete']:
            artifact_logs = ArtifactActivityLog.objects.select_related('user', 'artifact').all()
            if activity_type in ['upload', 'delete']:
                artifact_logs = artifact_logs.filter(action=activity_type)
            if username_search:
                artifact_logs = artifact_logs.filter(username__icontains=username_search)
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    date_from_aware = timezone.make_aware(date_from_obj)
                    artifact_logs = artifact_logs.filter(created_at__gte=date_from_aware)
                except ValueError:
                    pass
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    date_to_aware = timezone.make_aware(date_to_obj)
                    artifact_logs = artifact_logs.filter(created_at__lt=date_to_aware)
                except ValueError:
                    pass
            all_logs.extend(artifact_logs)
        
        # Sort by created_at (descending)
        all_logs_sorted = sorted(all_logs, key=attrgetter('created_at'), reverse=True)
        
        # Pagination
        paginator = Paginator(all_logs_sorted, 50)
        page_obj = paginator.get_page(page_number)
        
        # Serialize logs
        logs = []
        for log in page_obj:
            log_data = {
                'created_at': timezone.localtime(log.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': getattr(log, 'ip_address', None),
                'user_agent': getattr(log, 'user_agent', ''),
            }
            
            if isinstance(log, LoginAttempt):
                log_data.update({
                    'id': f'login-{log.id}',
                    'type': 'login',
                    'username': log.username,
                    'success': log.success,
                    'failure_reason': log.failure_reason if not log.success else None,
                })
            elif isinstance(log, DownloadLog):
                log_data.update({
                    'id': f'download-{log.id}',
                    'type': 'download',
                    'username': log.username,
                    'download_type': log.download_type,
                })
                if log.download_type == 'single' and log.artifact:
                    log_data['artifact'] = {
                        'filename': log.artifact.filename,
                        'product': log.artifact.product.name,
                        'category': log.artifact.category.name,
                        'version': log.artifact.version_string,
                    }
                elif log.download_type == 'bulk' and log.product:
                    log_data['bulk'] = {
                        'product': log.product.name,
                        'country': log.country.code if log.country else 'Global',
                        'artifact_count': log.artifact_count,
                    }
            elif isinstance(log, ArtifactActivityLog):
                log_data.update({
                    'id': f'artifact-{log.id}',  
                    'type': f'artifact_{log.action}',  # 'artifact_upload' or 'artifact_delete'
                    'username': log.username,
                    'action': log.action,
                    'action_display': log.get_action_display(),
                })
                if log.artifact:
                    log_data['artifact'] = {
                        'filename': log.artifact.filename,
                        'product': log.artifact.product.name,
                        'category': log.artifact.category.name,
                        'version': log.artifact.version_string,
                    }
                elif log.artifact_snapshot:
                    log_data['artifact'] = {
                        'filename': log.artifact_snapshot.get('filename', 'Unknown'),
                        'product': log.artifact_snapshot.get('product', 'Unknown'),
                        'category': log.artifact_snapshot.get('category', 'Unknown'),
                        'version': log.artifact_snapshot.get('version', 'Unknown'),
                        'deleted': True,
                    }
            
            logs.append(log_data)
        
        return JsonResponse({
            'success': True,
            'logs': logs,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


