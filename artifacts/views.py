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
    
    # 매트릭스 데이터 구성
    matrix_data = []
    for category in categories:
        row_data = {
            'category': category,
            'cells': []
        }
        
        for product in products:
            # 해당 국가/제품/카테고리의 최신 산출물 가져오기
            latest_artifact = Artifact.objects.filter(
                country=selected_country,
                product=product,
                category=category
            ).order_by('-created_at').first()  # 명시적으로 최신순 정렬
            
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
        'version': artifact.version_string,
        'filename': artifact.filename,
        'download_url': artifact.file.url if artifact.file else None,
    } for artifact in artifacts]
    
    return JsonResponse({
        'product': product.name,
        'category': category.name,
        'country': country.name if country else None,
        'history': history_data
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
    artifact = get_object_or_404(Artifact, id=artifact_id)
    
    if not artifact.file:
        return JsonResponse({'error': '파일이 존재하지 않습니다.'}, status=404)
    
    response = FileResponse(artifact.file.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{artifact.filename}"'
    return response


@login_required
@require_http_methods(["POST"])
def artifact_delete(request, artifact_id):
    """산출물 삭제 (Admin만)"""
    if not request.user.is_staff:
        return HttpResponseForbidden('권한이 없습니다.')
    
    artifact = get_object_or_404(Artifact, id=artifact_id)
    artifact.delete()
    
    return JsonResponse({
        'success': True,
        'message': '삭제되었습니다.'
    })
