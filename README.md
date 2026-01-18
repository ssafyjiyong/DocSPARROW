# DocSPARROW

기업 및 조직 내부 자료 관리 시스템

## 📋 개요

DocSPARROW는 제품별, 카테고리별, 국가별 산출물(문서)을 관리하는 웹 애플리케이션입니다.

## ✨ 주요 기능

- **매트릭스 대시보드**: 제품 × 카테고리 그리드 뷰
- **국가별 관리**: 한국, 미국, 일본, 스페인 지원
- **파일 업로드/다운로드**: 버전 관리 포함
- **히스토리 추적**: 산출물 업로드 이력 확인
- **사용자 인증**: 로그인/로그아웃, 비밀번호 변경

## 🛠️ 기술 스택

- **Backend**: Django 5.0
- **Frontend**: HTML, Tailwind CSS, Alpine.js
- **Database**: SQLite
- **Server**: Gunicorn + Nginx (프로덕션)

## 🚀 로컬 실행

```bash
# 가상환경 생성
python -m venv venv
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
python manage.py migrate

# 기본 데이터 로드 (국가, 제품, 카테고리)
python manage.py loaddata artifacts/fixtures/initial_data.json

# 서버 실행
python manage.py runserver
```

접속: http://127.0.0.1:8000

## 📦 프로덕션 배포

배포는 gunicorn과 nginx를 사용하여 실행됩니다.

```bash
# 간단 요약
gunicorn docsparrow.wsgi:application --bind 0.0.0.0:8000
```

## 📁 프로젝트 구조

```
docsparrow/
├── artifacts/          # 메인 앱
│   ├── templates/      # HTML 템플릿
│   ├── static/         # 정적 파일
│   └── views.py        # 뷰 로직
├── docsparrow/         # Django 설정
├── media/              # 업로드된 파일
└── manage.py
```

## 📄 라이선스

Internal Use Only
