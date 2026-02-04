from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
import os
from datetime import datetime


def artifact_upload_path(instance, filename):
    """
    커스텀 파일 업로드 경로 생성 함수
    원본 파일명을 보존하면서 타임스탬프 기반 디렉토리로 충돌 방지
    
    경로 형식: artifacts/%Y/%m/%d/%H%M%S_%f/{original_filename}
    예: artifacts/2026/01/30/152745_123456/Ent-SAST_제품 기능비교표_v2512.2.xlsx
    """
    now = datetime.now()
    # 초 단위 + 마이크로초를 사용하여 고유한 디렉토리 생성
    timestamp_dir = now.strftime('%Y/%m/%d/%H%M%S_%f')
    
    # 원본 파일명을 그대로 사용
    return os.path.join('artifacts', timestamp_dir, filename)



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
    file = models.FileField(upload_to=artifact_upload_path, verbose_name="파일")
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


class LoginAttempt(models.Model):
    """로그인 시도 기록 (Superuser 전용 조회)"""
    username = models.CharField(max_length=150, verbose_name="사용자명",
                               help_text="로그인 시도한 username (실패 시에도 기록)")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='login_attempts', verbose_name="사용자",
                            help_text="로그인 성공 시 User 객체")
    ip_address = models.GenericIPAddressField(verbose_name="IP 주소", null=True, blank=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True,
                                  help_text="브라우저 및 OS 정보")
    success = models.BooleanField(default=False, verbose_name="성공 여부")
    failure_reason = models.CharField(max_length=255, verbose_name="실패 이유",
                                     blank=True, help_text="로그인 실패 시 이유")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="시도 시간")

    class Meta:
        verbose_name = "로그인 시도"
        verbose_name_plural = "로그인 시도"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['username', '-created_at']),
            models.Index(fields=['success', '-created_at']),
        ]

    def __str__(self):
        status = "성공" if self.success else "실패"
        return f"{self.username} - {status} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class DownloadLog(models.Model):
    """다운로드 로그"""
    DOWNLOAD_TYPE_CHOICES = [
        ('single', '개별 다운로드'),
        ('bulk', '일괄 다운로드'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='downloads', verbose_name="사용자")
    username = models.CharField(max_length=150, verbose_name="사용자명",
                                help_text="다운로드한 사용자명")
    download_type = models.CharField(max_length=10, choices=DOWNLOAD_TYPE_CHOICES,
                                     verbose_name="다운로드 유형")
    
    # For single downloads
    artifact = models.ForeignKey(Artifact, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='download_logs', verbose_name="산출물")
    
    # For bulk downloads
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='bulk_downloads', verbose_name="제품")
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='bulk_downloads', verbose_name="국가")
    artifact_count = models.IntegerField(default=0, verbose_name="다운로드된 파일 수",
                                        help_text="일괄 다운로드 시 포함된 파일 개수")
    
    ip_address = models.GenericIPAddressField(verbose_name="IP 주소", null=True, blank=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True,
                                  help_text="브라우저 및 OS 정보")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="다운로드 시간")
    
    class Meta:
        verbose_name = "다운로드 로그"
        verbose_name_plural = "다운로드 로그"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['username', '-created_at']),
            models.Index(fields=['download_type', '-created_at']),
        ]
    
    def __str__(self):
        if self.download_type == 'single':
            return f"{self.username} - {self.artifact.filename if self.artifact else 'Unknown'} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
        else:
            return f"{self.username} - {self.product.name if self.product else 'Unknown'} 일괄 ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class ArtifactActivityLog(models.Model):
    """파일 활동 로그 (업로드/삭제)"""
    ACTION_CHOICES = [
        ('upload', '업로드'),
        ('delete', '삭제'),
    ]
    
    artifact = models.ForeignKey(Artifact, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='activity_logs', verbose_name="산출물",
                                help_text="삭제된 경우 NULL")
    
    # Snapshot of artifact info (for deleted files)
    artifact_snapshot = models.JSONField(verbose_name="파일 정보 스냅샷", null=True, blank=True,
                                        help_text="삭제 시 파일 정보 보존 (JSON)")
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='artifact_activities', verbose_name="사용자")
    username = models.CharField(max_length=150, verbose_name="사용자명")
    
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="활동 유형")
    
    ip_address = models.GenericIPAddressField(verbose_name="IP 주소", null=True, blank=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True,
                                  help_text="브라우저 및 OS 정보")
    
    details = models.JSONField(verbose_name="추가 정보", null=True, blank=True,
                              help_text="추가 메타데이터 (JSON)")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="활동 시간")
    
    class Meta:
        verbose_name = "파일 활동 로그"
        verbose_name_plural = "파일 활동 로그"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['username', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        action_display = self.get_action_display()
        if self.artifact:
            filename = self.artifact.filename
        elif self.artifact_snapshot:
            filename = self.artifact_snapshot.get('filename', 'Unknown')
        else:
            filename = 'Unknown'
        return f"{self.username} - {action_display}: {filename} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class Webhook(models.Model):
    """Discord 웹훅 모델 (Staff 전용)"""
    name = models.CharField(max_length=100, verbose_name="웹훅 이름",
                           help_text="웹훅을 식별하기 위한 이름")
    webhook_url = models.URLField(verbose_name="웹훅 URL",
                                  help_text="Discord 웹훅 URL")
    is_active = models.BooleanField(default=True, verbose_name="활성화",
                                    help_text="웹훅 활성화 여부")
    
    # Event type filters
    event_file_upload = models.BooleanField(default=True, verbose_name="파일 업로드 알림")
    event_file_delete = models.BooleanField(default=True, verbose_name="파일 삭제 알림")
    event_download_single = models.BooleanField(default=False, verbose_name="개별 다운로드 알림",
                                                help_text="개별 파일 다운로드 알림 (많을 수 있음)")
    event_download_bulk = models.BooleanField(default=True, verbose_name="일괄 다운로드 알림")
    event_admin_activity = models.BooleanField(default=True, verbose_name="관리자 활동 알림",
                                               help_text="카테고리/제품 관리, 셀 토글 등")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='webhooks_created', verbose_name="생성자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    class Meta:
        verbose_name = "웹훅"
        verbose_name_plural = "웹훅"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        status = "활성화" if self.is_active else "비활성화"
        return f"{self.name} ({status})"
    
    @property
    def masked_url(self):
        """웹훅 URL의 앞부분만 표시 (보안)"""
        if not self.webhook_url:
            return ""
        # https://discord.com/api/webhooks/... 형식
        parts = self.webhook_url.split('/')
        if len(parts) >= 6:
            return f"{'/'.join(parts[:6])}/..."
        return self.webhook_url[:30] + "..."
    
    @property
    def enabled_events(self):
        """활성화된 이벤트 목록"""
        events = []
        if self.event_file_upload:
            events.append("파일 업로드")
        if self.event_file_delete:
            events.append("파일 삭제")
        if self.event_download_single:
            events.append("개별 다운로드")
        if self.event_download_bulk:
            events.append("일괄 다운로드")
        if self.event_admin_activity:
            events.append("관리자 활동")
        return events
