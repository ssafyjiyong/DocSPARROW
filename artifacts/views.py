from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache, cache_control
from django.db.models import Max
from django.utils import timezone
from .models import Country, Product, ProductVersion, Category, Artifact
import json


def user_login(request):
    """사용자 로그인 뷰"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # 로그인 성공 시 항상 대시보드로 리다이렉트
            return redirect('artifacts:dashboard')
        else:
            return render(request, 'artifacts/login.html', {
                'error': '아이디 또는 비밀번호가 올바르지 않습니다.'
            })
    
    # 이미 로그인된 경우 대시보드로 리다이렉트
    if request.user.is_authenticated:
        return redirect('artifacts:dashboard')
    
    return render(request, 'artifacts/login.html')


def user_logout(request):
    """로그아웃 뷰"""
    logout(request)
    return redirect('artifacts:dashboard')


@login_required
def change_password(request):
    """비밀번호 변경 뷰"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # 비밀번호 변경 후 세션 유지
            update_session_auth_hash(request, user)
            messages.success(request, '비밀번호가 성공적으로 변경되었습니다.')
            return redirect('artifacts:dashboard')
        else:
            messages.error(request, '비밀번호 변경에 실패했습니다. 입력 내용을 확인해주세요.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'artifacts/change_password.html', {'form': form})


@login_required
@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def dashboard(request):
    """메인 대시보드 - 매트릭스 그리드 뷰"""
    # 국가 목록 가져오기
    countries = Country.objects.all()
    
    # 선택된 국가 가져오기 (GET 파라미터 또는 한국 기본값)
    country_code = request.GET.get('country')
    if country_code:
        selected_country = Country.objects.filter(code=country_code).first()
    else:
        # 기본값: 한국
        selected_country = Country.objects.filter(code='KR').first()
    
    products = Product.objects.all()
    categories = Category.objects.all()
    
    # Get version filters from GET params (format: version_1=1.0.0&version_2=1.1.0)
    version_filters = {}
    for product in products:
        version_param = request.GET.get(f'version_{product.id}')
        if version_param:
            version_filters[product.id] = version_param
    
    # Get all unique versions per product for this country
    product_versions = {}
    for product in products:
        versions = Artifact.objects.filter(
            country=selected_country,
            product=product
        ).values_list('version_string', flat=True).distinct().order_by('-version_string')
        product_versions[product.id] = list(versions)
    
    # 매트릭스 데이터 구성
    matrix_data = []
    for category in categories:
        row_data = {
            'category': category,
            'cells': []
        }
        
        for product in products:
            # Check if there's a version filter for this product
            version_filter = version_filters.get(product.id)
            
            # 해당 국가/제품/카테고리의 최신 산출물 가져오기
            query = Artifact.objects.filter(
                country=selected_country,
                product=product,
                category=category
            )
            
            # Apply version filter if specified
            if version_filter:
                query = query.filter(version_string=version_filter)
            
            latest_artifact = query.order_by('-created_at').first()
            
            row_data['cells'].append({
                'product': product,
                'artifact': latest_artifact,
            })
        
        matrix_data.append(row_data)
    
    context = {
        'countries': countries,
        'selected_country': selected_country,
        'products': products,
        'categories': categories,
        'matrix_data': matrix_data,
        'product_versions': product_versions,
        'version_filters': version_filters,
    }
    
    return render(request, 'artifacts/index.html', context)


@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def artifact_history(request, product_id, category_id):
    """특정 제품/카테고리의 산출물 히스토리 조회 (AJAX)"""
    product = get_object_or_404(Product, id=product_id)
    category = get_object_or_404(Category, id=category_id)
    
    # 국가 파라미터 가져오기 (기본값: 한국)
    country_code = request.GET.get('country')
    if country_code:
        country = Country.objects.filter(code=country_code).first()
    else:
        country = Country.objects.filter(code='KR').first()
    
    artifacts = Artifact.objects.filter(
        country=country,
        product=product,
        category=category
    ).select_related('uploader')
    
    history_data = [{
        'id': artifact.id,
        'created_at': timezone.localtime(artifact.created_at).strftime('%Y-%m-%d %H:%M'),
        'uploader': artifact.uploader.get_full_name() or artifact.uploader.username if artifact.uploader else 'Unknown',
        'uploader_id': artifact.uploader.id if artifact.uploader else None,
        'version': artifact.version_string,
        'filename': artifact.filename,
        'download_url': artifact.file.url if artifact.file else None,
    } for artifact in artifacts]
    
    return JsonResponse({
        'product': product.name,
        'category': category.name,
        'country': country.name if country else None,
        'history': history_data,
        'current_user_id': request.user.id if request.user.is_authenticated else None,
        'is_staff': request.user.is_staff if request.user.is_authenticated else False,
    })


@login_required
@require_http_methods(["POST"])
def artifact_upload(request, product_id, category_id):
    """산출물 업로드"""
    product = get_object_or_404(Product, id=product_id)
    category = get_object_or_404(Category, id=category_id)
    
    # 국가 파라미터 가져오기 (기본값: 한국)
    country_code = request.POST.get('country')
    if country_code:
        country = Country.objects.filter(code=country_code).first()
    else:
        country = Country.objects.filter(code='KR').first()
    
    version_string = request.POST.get('version_string')
    file = request.FILES.get('file')
    
    if not version_string or not file:
        return JsonResponse({'error': '버전과 파일을 모두 입력해주세요.'}, status=400)
    
    # Check for duplicate version
    existing = Artifact.objects.filter(
        country=country,
        product=product,
        category=category,
        version_string=version_string
    ).first()
    
    if existing:
        return JsonResponse({
            'error': f'버전 {version_string}이(가) 이미 존재합니다. 다른 버전을 입력해주세요.'
        }, status=400)
    
    artifact = Artifact.objects.create(
        country=country,
        product=product,
        category=category,
        version_string=version_string,
        file=file,
        uploader=request.user
    )
    
    return JsonResponse({
        'success': True,
        'message': '파일이 업로드되었습니다.',
        'artifact': {
            'id': artifact.id,
            'version': artifact.version_string,
            'filename': artifact.filename
        }
    })


def artifact_download(request, artifact_id):
    """산출물 다운로드"""
    from urllib.parse import quote
    
    artifact = get_object_or_404(Artifact, id=artifact_id)
    
    if not artifact.file:
        return JsonResponse({'error': '파일이 존재하지 않습니다.'}, status=404)
    
    response = FileResponse(artifact.file.open('rb'))
    # Support Korean filenames using RFC 5987
    encoded_filename = quote(artifact.filename)
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
    return response


def product_bulk_download(request, product_id):
    """제품별 산출물 일괄 다운로드 (ZIP)"""
    import zipfile
    import io
    from django.utils.text import slugify
    
    product = get_object_or_404(Product, id=product_id)
    
    # Get country parameter
    country_code = request.GET.get('country')
    if country_code:
        country = Country.objects.filter(code=country_code).first()
    else:
        country = Country.objects.filter(code='KR').first()
    
    # Get all artifacts for this product and country
    artifacts = Artifact.objects.filter(
        product=product,
        country=country
    ).select_related('category').order_by('category__display_order')
    
    if not artifacts.exists():
        return JsonResponse({'error': '다운로드할 자료가 없습니다.'}, status=404)
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for artifact in artifacts:
            if artifact.file:
                try:
                    # Create folder structure: category_name/filename
                    folder_name = slugify(artifact.category.name)
                    file_name = artifact.filename
                    archive_name = f"{folder_name}/{file_name}"
                    
                    # Add file to ZIP
                    with artifact.file.open('rb') as f:
                        zip_file.writestr(archive_name, f.read())
                except Exception as e:
                    # Skip files that can't be read
                    continue
    
    # Prepare response
    zip_buffer.seek(0)
    country_name = country.code if country else 'Global'
    filename = f"{slugify(product.name)}_{country_name}_saleskit.zip"
    
    response = FileResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["POST"])
def artifact_delete(request, artifact_id):
    """산출물 삭제 (Admin 또는 업로더)"""
    artifact = get_object_or_404(Artifact, id=artifact_id)
    
    # Allow admin or uploader to delete
    if not (request.user.is_staff or artifact.uploader == request.user):
        return HttpResponseForbidden('권한이 없습니다.')
    
    artifact.delete()
    
    return JsonResponse({
        'success': True,
        'message': '삭제되었습니다.'
    })
