# 사용자 계정 일괄 생성 가이드

## 🔒 보안 우선 접근 방식

사용자 계정 정보(이메일, 비밀번호)는 **Git에 절대 올리지 않습니다**.

- ✅ **Git에 올리는 것**: `users.json.example` (예제 템플릿)
- ❌ **Git에 올리지 않는 것**: `users.json` (실제 사용자 데이터)

---

## 방법 1: JSON 파일 사용 (추천 ⭐)

### 1단계: users.json 파일 생성

VM 서버에서 실제 사용자 데이터 파일을 생성합니다:

```bash
cd /opt/docsparrow

# 예제 파일을 복사
cp users.json.example users.json

# 파일 편집
nano users.json
```

`users.json` 예시:

```json
[
  {
    "username": "admin",
    "email": "admin@your-company.com",
    "password": "Strong!P@ssw0rd#2024",
    "is_staff": true,
    "is_superuser": true,
    "first_name": "관리자",
    "last_name": ""
  },
  {
    "username": "consulting",
    "email": "consulting@your-company.com",
    "password": "Consulting!Pass#123",
    "is_staff": true,
    "is_superuser": false,
    "first_name": "컨설팅",
    "last_name": "팀"
  }
]
```

### 2단계: 사용자 생성

```bash
source venv/bin/activate
python manage.py create_users
```

### 3단계: 생성 확인

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
User.objects.all().values('username', 'email', 'is_staff', 'is_superuser')
```

---

## 방법 2: 커스텀 JSON 파일 경로 지정

다른 위치의 JSON 파일을 사용할 수도 있습니다:

```bash
# 특정 경로의 JSON 파일 사용
python manage.py create_users --file /secure/path/production_users.json

# 또는 상대 경로
python manage.py create_users --file config/users.json
```

---

## VM 재배포 시 자동화 스크립트

기존 재배포 스크립트에 사용자 생성을 추가:

```bash
#!/bin/bash
# reset_deployment.sh

echo "=== DocSPARROW 재배포 시작 ==="

# 서비스 중지
sudo systemctl stop gunicorn

# 프로젝트 디렉토리로 이동
cd /opt/docsparrow
source venv/bin/activate

# 최신 코드 가져오기
echo "Git pull..."
git pull origin main

# 백업
echo "데이터 백업 중..."
mkdir -p backups
cp db.sqlite3 "backups/db.sqlite3.$(date +%Y%m%d_%H%M%S)" 2>/dev/null
tar -czf "backups/media_$(date +%Y%m%d).tar.gz" media/ 2>/dev/null

# 기존 데이터 삭제
echo "기존 데이터 삭제..."
rm -f db.sqlite3
rm -rf media/artifacts/*

# 데이터베이스 재생성
echo "데이터베이스 마이그레이션..."
python manage.py migrate

# 기본 데이터 로드
echo "기본 데이터 로드..."
python manage.py loaddata artifacts/fixtures/initial_data.json

# 사용자 계정 일괄 생성
echo "사용자 계정 생성..."
python manage.py create_users

# 정적 파일 수집
echo "정적 파일 수집..."
python manage.py collectstatic --noinput

# 권한 재설정
echo "권한 재설정..."
sudo chmod 664 db.sqlite3
sudo chown ubuntu:www-data db.sqlite3
sudo chmod -R 775 media
sudo chown -R ubuntu:www-data media

# 서비스 재시작
echo "서비스 재시작..."
sudo systemctl restart gunicorn

# 상태 확인
sleep 2
sudo systemctl status gunicorn --no-pager

echo "=== 재배포 완료 ==="
echo ""
echo "생성된 계정:"
echo "  admin / admin1234 (슈퍼유저)"
echo "  consulting / consulting1234 (스태프)"
echo "  business / business1234 (일반)"
echo "  marketing / marketing1234 (일반)"
echo "  user1 / user1234 (일반)"
```

---

## 보안 권장사항

### 프로덕션 환경에서는 반드시:

1. **강력한 비밀번호 사용**
   ```python
   'password': 'Strong!P@ssw0rd#2024'
   ```

2. **초기 로그인 후 비밀번호 변경 강제**
   - Django의 `password_change` 뷰 활용

3. **민감한 정보 환경 변수화**
   ```python
   import os
   'password': os.getenv('ADMIN_PASSWORD', 'default_pwd')
   ```

4. **Git에서 제외**
   ```bash
   # .gitignore
   artifacts/management/commands/create_users.py  # 프로덕션 비밀번호 포함 시
   ```

---

## 트러블슈팅

### "User already exists" 에러
- 기존 사용자를 먼저 삭제하거나
- Command가 자동으로 건너뜀 (중복 방지)

### Permission denied
```bash
# Django 앱 권한 확인
sudo chown -R ubuntu:www-data /opt/docsparrow
```

### 사용자가 로그인되지 않음
```bash
# Django shell에서 확인
python manage.py shell
```

```python
from django.contrib.auth.models import User
users = User.objects.all()
for user in users:
    print(f"{user.username}: active={user.is_active}, staff={user.is_staff}")
```
