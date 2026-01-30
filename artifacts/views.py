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
from .models import Country, Product, ProductVersion, Category, Artifact, ProductCategoryDisabled, LoginAttempt, ArtifactActivityLog, DownloadLog
import json


def get_client_ip(request):
    """클라이언트의 실제 IP 주소를 가져옵니다 (프록시 고려)"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """클라이언트의 User-Agent를 가져옵니다"""
    return request.META.get('HTTP_USER_AGENT', '')[:500]  # 최대 500자로 제한


def user_login(request):
    """사용자 로그인 뷰"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        # IP 주소와 User-Agent 추출
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        if user is not None:
            login(request, user)
            
            # 로그인 성공 기록
            LoginAttempt.objects.create(
                username=username,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            # 로그인 성공 시 항상 대시보드로 리다이렉트
            return redirect('artifacts:dashboard')
        else:
            # 로그인 실패 기록
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='잘못된 사용자명 또는 비밀번호'
            )
            
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
    
    # 부서 필터 가져오기
    selected_department = request.GET.get('department', '')
    
    # 부서 목록
    departments = [
        ('', '전체 부서'),
        ('consulting', '컨설팅'),
        ('business', '사업'),
        ('marketing', '마케팅'),
    ]
    
    products = Product.objects.all()
    
    # 카테고리 필터링 (부서별)
    if selected_department:
        categories = Category.objects.filter(department=selected_department)
    else:
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
    
    # Get disabled cells for the selected country
    disabled_cells = ProductCategoryDisabled.objects.filter(
        country=selected_country
    ).select_related('product', 'category')
    disabled_set = {(dc.product.id, dc.category.id) for dc in disabled_cells}
    
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
            
            latest_artifact = query.order_by('-version_string').first()
            
            # Check if this cell is disabled
            is_disabled = (product.id, category.id) in disabled_set
            
            row_data['cells'].append({
                'product': product,
                'artifact': latest_artifact,
                'is_disabled': is_disabled,
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
        'departments': departments,
        'selected_department': selected_department,
        'disabled_set': disabled_set,
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
    ).select_related('uploader').order_by('-version_string')
    
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
    
    # Check if this cell is disabled for this specific country
    is_disabled = ProductCategoryDisabled.objects.filter(
        country=country,
        product=product,
        category=category
    ).exists()
    
    if is_disabled:
        return JsonResponse({'error': '이 셀은 해당 없음으로 설정되어 업로드가 불가능합니다.'}, status=403)
    
    version_string = request.POST.get('version_string')
    file = request.FILES.get('file')
    
    if not version_string or not file:
        return JsonResponse({'error': '버전과 파일을 모두 입력해주세요.'}, status=400)
    
    # Validate filename format: 제품명_카테고리명_버전명.확장자
    # US의 경우: EN_제품명_카테고리명_버전명.확장자
    # Note: 파일명에서 공백은 언더스코어(_)로 대체 가능
    filename = file.name
    filename_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Expected format based on country
    if country and country.code == 'US':
        # US format: EN_ProductName_CategoryName_vX.Y.Z
        expected_prefix = f"EN_{product.name}_{category.name}_v{version_string}"
    else:
        # Default (KR) format: ProductName_CategoryName_vX.Y.Z
        expected_prefix = f"{product.name}_{category.name}_v{version_string}"
    
    # Normalize both filenames: replace spaces with underscores for comparison
    # This allows users to use either spaces or underscores in filenames
    normalized_expected = expected_prefix.replace(' ', '_')
    normalized_actual = filename_without_ext.replace(' ', '_')
    
    if normalized_actual != normalized_expected:
        return JsonResponse({
            'error': f'파일명 양식이 올바르지 않습니다.\n\n'
                    f'올바른 형식: {expected_prefix.replace(" ", "_")}.확장자\n'
                    f'현재 파일명: {filename}'
        }, status=400)
    
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
    
    # Log upload activity
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    ArtifactActivityLog.objects.create(
        artifact=artifact,
        user=request.user,
        username=request.user.username,
        action='upload',
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'country': country.code if country else None,
            'product': product.name,
            'category': category.name,
            'version': version_string,
            'filename': artifact.filename
        }
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
    
    # Log the download
    DownloadLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        download_type='single',
        artifact=artifact,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
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
    
    # Get version filter if provided
    version_filter = request.GET.get('version')
    
    # Build query
    query = Artifact.objects.filter(
        product=product,
        country=country
    )
    
    # Apply version filter if specified
    if version_filter:
        query = query.filter(version_string=version_filter)
    
    # Get all artifacts for this product and country
    artifacts = query.select_related('category').order_by('category__display_order')
    
    if not artifacts.exists():
        return JsonResponse({'error': '다운로드할 자료가 없습니다.'}, status=404)
    
    # Count artifacts for logging
    artifact_count = artifacts.count()
    
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
    
    # Log the bulk download
    DownloadLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        download_type='bulk',
        product=product,
        country=country,
        artifact_count=artifact_count,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
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
    
    # Save artifact info before deletion for logging
    artifact_snapshot = {
        'id': artifact.id,
        'filename': artifact.filename,
        'country': artifact.country.code if artifact.country else None,
        'product': artifact.product.name,
        'category': artifact.category.name,
        'version': artifact.version_string,
        'uploader': artifact.uploader.username if artifact.uploader else None
    }
    
    # Get IP and User-Agent
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Delete the artifact
    artifact.delete()
    
    # Log deletion activity (artifact is now None)
    ArtifactActivityLog.objects.create(
        artifact=None,  # File is deleted
        artifact_snapshot=artifact_snapshot,
        user=request.user,
        username=request.user.username,
        action='delete',
        ip_address=ip_address,
        user_agent=user_agent,
        details={'deleted_by_role': 'admin' if request.user.is_staff else 'uploader'}
    )
    
    return JsonResponse({
        'success': True,
        'message': '삭제되었습니다.'
    })
