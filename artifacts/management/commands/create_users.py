import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.conf import settings


class Command(BaseCommand):
    help = 'JSON 파일에서 사용자 계정 정보를 읽어 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='기존 사용자 계정들을 삭제합니다 (슈퍼유저 제외)',
        )
        parser.add_argument(
            '--file',
            type=str,
            default='users.json',
            help='사용자 데이터 JSON 파일 경로 (기본: users.json)',
        )

    def get_users_data(self, json_file):
        """JSON 파일 또는 기본 예제 데이터를 로드"""
        json_path = os.path.join(settings.BASE_DIR, json_file)
        
        # JSON 파일이 존재하면 로드
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ "{json_file}" 파일에서 사용자 데이터를 로드했습니다.')
                    )
                    return data
            except json.JSONDecodeError as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ JSON 파일 파싱 오류: {e}')
                )
                return []
        
        # JSON 파일이 없으면 경고하고 예제 데이터 반환
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  "{json_file}" 파일을 찾을 수 없습니다.\n'
                f'예제 데이터를 사용합니다. (개발/테스트 환경 전용)\n'
                f'\n프로덕션 환경에서는 반드시 별도의 users.json 파일을 생성하세요!\n'
                f'예제: users.json.example 참고\n'
            )
        )
        
        # 기본 예제 데이터 (개발/테스트용)
        return [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'changeme123',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'User',
            },
        ]

    def handle(self, *args, **options):
        json_file = options['file']
        
        if options['delete']:
            # 슈퍼유저가 아닌 사용자만 삭제
            deleted_count = User.objects.filter(is_superuser=False).delete()[0]
            self.stdout.write(
                self.style.WARNING(f'✓ {deleted_count}개의 일반 사용자를 삭제했습니다.')
            )
            return

        # 사용자 데이터 로드
        users = self.get_users_data(json_file)
        
        if not users:
            self.stdout.write(
                self.style.ERROR('사용자 데이터가 없습니다.')
            )
            return

        created_count = 0
        skipped_count = 0
        
        for user_data in users:
            username = user_data.get('username')
            
            if not username:
                self.stdout.write(
                    self.style.ERROR('✗ username이 없는 사용자 데이터를 건너뜁니다.')
                )
                continue
            
            try:
                # 이미 존재하는지 확인
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.WARNING(f'⊙ 사용자 "{username}"는 이미 존재합니다. 건너뜁니다.')
                    )
                    skipped_count += 1
                    continue
                
                # 사용자 생성
                if user_data.get('is_superuser', False):
                    user = User.objects.create_superuser(
                        username=user_data['username'],
                        email=user_data.get('email', ''),
                        password=user_data.get('password', 'changeme123')
                    )
                else:
                    user = User.objects.create_user(
                        username=user_data['username'],
                        email=user_data.get('email', ''),
                        password=user_data.get('password', 'changeme123')
                    )
                    user.is_staff = user_data.get('is_staff', False)
                    user.first_name = user_data.get('first_name', '')
                    user.last_name = user_data.get('last_name', '')
                    user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 사용자 "{username}" 생성 완료')
                )
                created_count += 1
                
            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ 사용자 "{username}" 생성 실패: {e}')
                )
        
        # 최종 결과 출력
        self.stdout.write(self.style.SUCCESS(f'\n=== 작업 완료 ==='))
        self.stdout.write(f'생성: {created_count}명')
        self.stdout.write(f'건너뜀: {skipped_count}명')
        self.stdout.write(self.style.SUCCESS(f'총 {created_count + skipped_count}명의 사용자 처리'))
