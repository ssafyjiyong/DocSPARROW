# 🔐 사용자 계정 관리

DocSPARROW의 사용자 계정을 안전하게 관리하는 방법입니다.

## 빠른 시작

### 1. VM에서 사용자 JSON 파일 생성

```bash
cd /opt/docsparrow
cp users.json.example users.json
nano users.json  # 실제 정보로 수정
```

### 2. 사용자 생성

```bash
source venv/bin/activate
python manage.py create_users
```

### 3. 완료!

로그인 테스트: `http://your-server-ip/accounts/login`

---

## 🔒 보안 원칙

| 파일 | Git 추적 | 용도 |
|------|---------|------|
| `users.json.example` | ✅ YES | 예제 템플릿 (개인정보 없음) |
| `users.json` | ❌ NO | 실제 사용자 데이터 (개인정보 포함) |

`.gitignore`에 `users.json`이 등록되어 있어 실수로 커밋되지 않습니다.

---

## 명령어 모음

### 사용자 생성
```bash
python manage.py create_users
```

### 사용자 삭제 (슈퍼유저 제외)
```bash
python manage.py create_users --delete
```

### 커스텀 파일 경로 사용
```bash
python manage.py create_users --file /path/to/custom_users.json
```

### 사용자 목록 확인
```bash
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.values_list('username', 'is_superuser', 'is_staff'))"
```

---

## JSON 파일 형식

```json
[
  {
    "username": "사용자ID",
    "email": "email@domain.com",
    "password": "비밀번호",
    "is_staff": true,        // 스태프 권한
    "is_superuser": false,   // 슈퍼유저 권한
    "first_name": "이름",
    "last_name": "성"
  }
]
```

### 필수 필드
- `username`: 사용자 ID

### 선택 필드
- `email`: 이메일 (기본: 빈 문자열)
- `password`: 비밀번호 (기본: `changeme123`)
- `is_staff`: 스태프 권한 (기본: `false`)
- `is_superuser`: 슈퍼유저 권한 (기본: `false`)
- `first_name`: 이름 (기본: 빈 문자열)
- `last_name`: 성 (기본: 빈 문자열)

---

## 재배포 자동화

`reset_deployment.sh`에 사용자 생성 포함:

```bash
#!/bin/bash
cd /opt/docsparrow
source venv/bin/activate

# ... (마이그레이션, 데이터 로드 등) ...

# 사용자 자동 생성
python manage.py create_users

# ... (권한 설정, 서비스 재시작 등) ...
```

---

## 트러블슈팅

### "파일을 찾을 수 없습니다" 경고
- `users.json` 파일이 프로젝트 루트에 없습니다
- 예제 데이터(개발용)로 단일 admin 계정만 생성됩니다
- **프로덕션에서는 반드시 users.json 파일을 생성하세요**

### "User already exists" 메시지
- 정상입니다. 중복 사용자는 자동으로 건너뜁니다
- 기존 사용자를 삭제하려면: `--delete` 옵션 사용

### JSON 파싱 오류
```bash
# JSON 유효성 검사
python -m json.tool users.json
```

---

## 보안 권장사항

### ✅ 해야 할 것

1. **강력한 비밀번호 사용**
   - 최소 12자 이상
   - 대문자, 소문자, 숫자, 특수문자 포함
   - 예: `Strong!P@ssw0rd#2024`

2. **실제 회사 이메일 사용**
   - `admin@your-company.com`
   - 비밀번호 재설정 등에 필요

3. **파일 권한 제한**
   ```bash
   chmod 600 users.json
   ```

4. **정기적인 비밀번호 변경**
   - Django Admin에서 변경 가능
   - `/admin/auth/user/`

### ❌ 하지 말아야 할 것

1. **Git에 users.json 커밋**
   - `.gitignore`에 등록되어 있으나 주의

2. **단순한 비밀번호**
   - `admin1234`, `password123` 같은 쉬운 비밀번호

3. **프로덕션에서 예제 데이터 사용**
   - 반드시 `users.json` 파일 생성

---

## 개발 vs 프로덕션

### 개발 환경 (로컬)
```bash
# users.json 없이 실행 → 예제 데이터 사용
python manage.py create_users

# 생성되는 계정: admin / changeme123
```

### 프로덕션 환경 (VM)
```bash
# 반드시 users.json 생성 후 실행
cp users.json.example users.json
nano users.json  # 실제 정보 입력
python manage.py create_users
```

---

자세한 내용은 [`user-creation-guide.md`](docs/user-creation-guide.md)를 참고하세요.
