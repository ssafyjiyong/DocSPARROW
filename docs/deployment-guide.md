# DocSPARROW VM 배포 가이드

이 가이드는 DocSPARROW 애플리케이션을 Ubuntu 22.04 VM에 Gunicorn과 Nginx를 사용하여 배포하는 전체 프로세스를 설명합니다.

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [서버 초기 설정](#서버-초기-설정)
3. [애플리케이션 설치](#애플리케이션-설치)
4. [Gunicorn 설정](#gunicorn-설정)
5. [Nginx 설정](#nginx-설정)
6. [보안 설정](#보안-설정)
7. [운영 및 관리](#운영-및-관리)

---

## 시스템 요구사항

### 하드웨어
- **CPU**: 2 Core 이상
- **RAM**: 4GB 이상 권장
- **디스크**: 20GB 이상 (미디어 파일 저장 공간 고려)

### 소프트웨어
- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.10 이상
- **데이터베이스**: SQLite (기본) 또는 PostgreSQL

---

## 서버 초기 설정

### 1. 시스템 업데이트

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 필수 패키지 설치

```bash
sudo apt install -y python3-pip python3-venv nginx git
```

### 3. 배포 사용자 생성 (선택)

```bash
# 배포 전용 사용자 생성
sudo adduser docsparrow
sudo usermod -aG sudo docsparrow

# 사용자 전환
su - docsparrow
```

---

## 애플리케이션 설치

### 1. 프로젝트 클론

```bash
cd /home/docsparrow
git clone https://github.com/ssafyjiyong/DocSPARROW.git
cd DocSPARROW
```

### 2. 가상환경 생성 및 활성화

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 4. Django 설정

#### 4.1 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=your-secret-key-here-change-this
ALLOWED_HOSTS=your-domain.com,your-server-ip
DATABASE_URL=sqlite:///db.sqlite3
EOF
```

> **⚠️ 중요**: `SECRET_KEY`는 반드시 안전한 값으로 변경하세요.
> 생성 방법: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`

#### 4.2 settings.py 수정

`docsparrow/settings.py`에서 프로덕션 설정 추가:

```python
import os
from pathlib import Path

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')

# ALLOWED_HOSTS
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
```

### 5. 데이터베이스 마이그레이션 및 정적 파일 수집

```bash
# 마이그레이션 실행
python manage.py migrate

# 기본 데이터 자동 로드 (국가, 제품, 카테고리)
python manage.py loaddata artifacts/fixtures/initial_data.json

# 관리자 계정 생성
python manage.py createsuperuser

# 정적 파일 수집
python manage.py collectstatic --noinput
```

> **💡 참고**: `initial_data.json` fixtures는 4개 국가(한국, 미국, 일본, 스페인), 10개 제품, 17개 카테고리를 자동으로 생성합니다. 재배포 시마다 수동으로 데이터를 입력할 필요가 없습니다.

### 6. 미디어 디렉토리 권한 설정

```bash
# 미디어 디렉토리 생성 및 권한 설정
mkdir -p media/artifacts
sudo chown -R docsparrow:www-data media
sudo chmod -R 775 media
```

---

## Gunicorn 설정

### 1. Gunicorn 테스트

```bash
# 가상환경 활성화 상태에서
cd /home/docsparrow/DocSPARROW
gunicorn --bind 0.0.0.0:8000 docsparrow.wsgi:application
```

브라우저에서 `http://your-server-ip:8000` 접속하여 확인 후 `Ctrl+C`로 종료

### 2. Gunicorn Systemd 서비스 생성

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

다음 내용 입력:

```ini
[Unit]
Description=gunicorn daemon for DocSPARROW
After=network.target

[Service]
User=docsparrow
Group=www-data
WorkingDirectory=/home/docsparrow/DocSPARROW
Environment="PATH=/home/docsparrow/DocSPARROW/venv/bin"
EnvironmentFile=/home/docsparrow/DocSPARROW/.env
ExecStart=/home/docsparrow/DocSPARROW/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/docsparrow/DocSPARROW/gunicorn.sock \
          --timeout 120 \
          --access-logfile /var/log/gunicorn/access.log \
          --error-logfile /var/log/gunicorn/error.log \
          docsparrow.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 3. 로그 디렉토리 생성

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown docsparrow:www-data /var/log/gunicorn
```

### 4. Gunicorn 서비스 시작 및 활성화

```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

---

## Nginx 설정

### 1. Nginx 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/docsparrow
```

다음 내용 입력:

```nginx
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    client_max_body_size 100M;

    # 정적 파일
    location /static/ {
        alias /home/docsparrow/DocSPARROW/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 미디어 파일
    location /media/ {
        alias /home/docsparrow/DocSPARROW/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # 애플리케이션
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/docsparrow/DocSPARROW/gunicorn.sock;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

### 2. 심볼릭 링크 생성 및 Nginx 재시작

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/docsparrow /etc/nginx/sites-enabled/

# 기본 사이트 비활성화 (선택)
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 3. 방화벽 설정

```bash
# UFW 방화벽 설정 (Ubuntu)
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 보안 설정

### 1. SSL/TLS 인증서 설정 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급 및 자동 설정
sudo certbot --nginx -d your-domain.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

### 2. 파일 권한 점검

```bash
# 프로젝트 파일 권한
sudo chown -R docsparrow:www-data /home/docsparrow/DocSPARROW
sudo chmod -R 755 /home/docsparrow/DocSPARROW

# 미디어 디렉토리는 쓰기 권한 필요
sudo chmod -R 775 /home/docsparrow/DocSPARROW/media

# SQLite 데이터베이스 권한
sudo chmod 664 /home/docsparrow/DocSPARROW/db.sqlite3
sudo chown docsparrow:www-data /home/docsparrow/DocSPARROW/db.sqlite3
```

### 3. 환경 변수 보안

```bash
# .env 파일 권한 제한
chmod 600 /home/docsparrow/DocSPARROW/.env
```

---

## 운영 및 관리

### 서비스 관리 명령어

```bash
# Gunicorn 서비스
sudo systemctl status gunicorn    # 상태 확인
sudo systemctl start gunicorn     # 시작
sudo systemctl stop gunicorn      # 중지
sudo systemctl restart gunicorn   # 재시작
sudo journalctl -u gunicorn -f    # 로그 확인

# Nginx 서비스
sudo systemctl status nginx       # 상태 확인
sudo systemctl restart nginx      # 재시작
sudo nginx -t                     # 설정 테스트
```

### 애플리케이션 업데이트

```bash
cd /home/docsparrow/DocSPARROW
source venv/bin/activate

# 코드 업데이트
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt

# 마이그레이션 실행
python manage.py migrate

# 정적 파일 수집
python manage.py collectstatic --noinput

# Gunicorn 재시작
sudo systemctl restart gunicorn
```

### 로그 확인

```bash
# Gunicorn 로그
tail -f /var/log/gunicorn/access.log
tail -f /var/log/gunicorn/error.log

# Nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Django 로그 (settings.py에서 설정 시)
tail -f /home/docsparrow/DocSPARROW/logs/django.log
```

### 데이터베이스 백업

```bash
# SQLite 백업
cd /home/docsparrow/DocSPARROW
cp db.sqlite3 "backups/db.sqlite3.$(date +%Y%m%d_%H%M%S)"

# 미디어 파일 백업
tar -czf "backups/media_$(date +%Y%m%d).tar.gz" media/
```

### 성능 모니터링

```bash
# 시스템 리소스 확인
htop

# Gunicorn 프로세스 확인
ps aux | grep gunicorn

# 디스크 사용량 확인
df -h

# 메모리 사용량 확인
free -h
```

---

## 문제 해결

### Gunicorn 소켓 연결 실패

```bash
# 소켓 파일 확인
ls -la /home/docsparrow/DocSPARROW/gunicorn.sock

# 권한 재설정
sudo systemctl restart gunicorn
```

### 502 Bad Gateway

```bash
# Gunicorn 상태 확인
sudo systemctl status gunicorn

# 로그 확인
sudo journalctl -u gunicorn -n 50

# 소켓 파일 권한 확인
sudo chown docsparrow:www-data /home/docsparrow/DocSPARROW/gunicorn.sock
```

### 파일 업로드 실패

```bash
# 미디어 디렉토리 권한 확인
sudo chmod -R 775 /home/docsparrow/DocSPARROW/media
sudo chown -R docsparrow:www-data /home/docsparrow/DocSPARROW/media

# Nginx 업로드 크기 제한 확인 (nginx.conf)
client_max_body_size 100M;
```

### 정적 파일 로딩 실패

```bash
# 정적 파일 재수집
cd /home/docsparrow/DocSPARROW
source venv/bin/activate
python manage.py collectstatic --noinput

# Nginx 설정 확인
sudo nginx -t
sudo systemctl restart nginx
```

---

## 체크리스트

배포 전 확인사항:

- [ ] `.env` 파일에 `SECRET_KEY` 설정
- [ ] `.env` 파일에 `ALLOWED_HOSTS` 설정
- [ ] `DEBUG=False` 설정
- [ ] 데이터베이스 마이그레이션 완료
- [ ] 정적 파일 수집 완료
- [ ] 미디어 디렉토리 권한 설정
- [ ] Gunicorn 서비스 정상 작동
- [ ] Nginx 설정 테스트 통과
- [ ] SSL 인증서 설치 (프로덕션)
- [ ] 방화벽 설정 완료
- [ ] 백업 스크립트 설정

---

## 참고 자료

- [Django 공식 배포 가이드](https://docs.djangoproject.com/en/5.0/howto/deployment/)
- [Gunicorn 문서](https://docs.gunicorn.org/)
- [Nginx 문서](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)

---

**작성일**: 2026-01-18  
**버전**: 1.0  
**프로젝트**: DocSPARROW
