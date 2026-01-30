# DocSPARROW

제품 문서를 한곳에서 관리하는 시스템입니다.

## 주요 기능

- **매트릭스 뷰**: 제품과 문서 카테고리를 한눈에 볼 수 있는 그리드 대시보드
- **버전 관리**: 문서 버전별 업로드 이력 추적 및 다운로드
- **국가별 관리**: 한국, 미국, 일본, 스페인 등 국가별 문서 관리
- **사용자 관리**: 로그인 추적, 비밀번호 변경, 권한 관리
- **관리자 기능**: 로그인 이력 확인 (슈퍼유저 전용)

## 기술 스택

- Django 5.0
- SQLite
- Tailwind CSS + Alpine.js
- Gunicorn (프로덕션)

## 시작하기

```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# DB 마이그레이션
python manage.py migrate

# 초기 데이터 로드
python manage.py loaddata artifacts/fixtures/initial_data.json

# 개발 서버 실행
python manage.py runserver
```

접속: http://127.0.0.1:8000

## 프로덕션 배포

```bash
gunicorn docsparrow.wsgi:application --bind 0.0.0.0:8000
```

## 프로젝트 구조

```
docsparrow/
├── artifacts/      # 메인 앱 (모델, 뷰, 템플릿)
├── docsparrow/     # 프로젝트 설정
├── media/          # 업로드 파일 저장소
└── manage.py
```

## 라이선스

Internal Use Only
