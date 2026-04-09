"""
LDAP/Active Directory Authentication Backend using ldap3

ldap3는 순수 Python LDAP 라이브러리로, python-ldap과 달리
C 컴파일러 없이 모든 Python 버전에서 설치 가능합니다.

동작 방식:
1. 사용자가 입력한 username@fasoo.com 으로 AD에 Direct Bind 시도
2. Bind 성공 시 AD에서 사용자 정보(이름, 이메일) 조회
3. Django User 객체 자동 생성 또는 업데이트
4. Bind 실패 시 None 반환 → Django가 다음 백엔드(ModelBackend)로 Fallback
"""
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPException

logger = logging.getLogger('ldap_auth')
User = get_user_model()


class LDAPBackend:
    """
    Active Directory LDAP 인증 백엔드 (ldap3 기반)
    
    settings.py에서 다음 설정을 사용합니다:
        LDAP_SERVER_URI: AD 서버 주소 (예: ldap://192.168.200.5:389)
        LDAP_USER_DN_TEMPLATE: Direct Bind 템플릿 (예: %(user)s@fasoo.com)
        LDAP_USER_SEARCH_BASE: 사용자 검색 Base DN
        LDAP_USER_ATTR_MAP: AD 속성 → Django User 필드 매핑
        LDAP_ALWAYS_UPDATE_USER: 로그인 시 매번 User 업데이트 여부
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """AD 서버에 Direct Bind로 인증 시도"""
        if not username or not password:
            return None
        
        server_uri = getattr(settings, 'LDAP_SERVER_URI', '')
        if not server_uri:
            return None
        
        # Direct Bind: username@domain.com 형식으로 바인드
        dn_template = getattr(settings, 'LDAP_USER_DN_TEMPLATE', '%(user)s@fasoo.com')
        bind_dn = dn_template % {'user': username}
        
        try:
            # AD 서버 연결
            server = Server(server_uri, get_info=ALL, connect_timeout=5)
            conn = Connection(
                server,
                user=bind_dn,
                password=password,
                auto_bind=True,
                read_only=True,
                receive_timeout=5,
            )
            
            logger.info(f"LDAP 인증 성공: {username}")
            
            # 사용자 정보 조회
            user_info = self._get_user_info(conn, username)
            
            # Django User 생성/업데이트
            user = self._get_or_create_user(username, user_info)
            
            conn.unbind()
            return user
            
        except LDAPException as e:
            logger.warning(f"LDAP 인증 실패: {username} - {e}")
            return None
        except Exception as e:
            logger.error(f"LDAP 오류: {username} - {e}")
            return None
    
    def _get_user_info(self, conn, username):
        """AD에서 사용자 정보 검색"""
        search_base = getattr(
            settings, 'LDAP_USER_SEARCH_BASE', 'OU=FASOOCOM,DC=fasoo,DC=com'
        )
        
        try:
            conn.search(
                search_base=search_base,
                search_filter=f'(sAMAccountName={username})',
                search_scope=SUBTREE,
                attributes=['cn', 'sn', 'givenName', 'mail', 'userPrincipalName'],
            )
            
            if conn.entries:
                entry = conn.entries[0]
                return {
                    'cn': str(entry.cn) if hasattr(entry, 'cn') else '',
                    'sn': str(entry.sn) if hasattr(entry, 'sn') else '',
                    'givenName': str(entry.givenName) if hasattr(entry, 'givenName') else '',
                    'mail': str(entry.mail) if hasattr(entry, 'mail') else '',
                    'userPrincipalName': str(entry.userPrincipalName) if hasattr(entry, 'userPrincipalName') else '',
                }
        except Exception as e:
            logger.warning(f"LDAP 사용자 정보 조회 실패: {username} - {e}")
        
        return {}
    
    def _get_or_create_user(self, username, user_info):
        """Django User 객체 생성 또는 업데이트"""
        attr_map = getattr(settings, 'LDAP_USER_ATTR_MAP', {
            'first_name': 'cn',
            'last_name': 'sn',
            'email': 'userPrincipalName',
        })
        
        always_update = getattr(settings, 'LDAP_ALWAYS_UPDATE_USER', True)
        
        try:
            user = User.objects.get(username=username)
            
            # 기존 사용자 정보 업데이트
            if always_update and user_info:
                updated = False
                for django_field, ldap_attr in attr_map.items():
                    ldap_value = user_info.get(ldap_attr, '')
                    if ldap_value and getattr(user, django_field, '') != ldap_value:
                        setattr(user, django_field, ldap_value)
                        updated = True
                if updated:
                    user.save()
                    logger.info(f"LDAP 사용자 정보 업데이트: {username}")
                    
        except User.DoesNotExist:
            # 새 사용자 생성 (동적 사용자 생성)
            user_data = {'username': username}
            for django_field, ldap_attr in attr_map.items():
                ldap_value = user_info.get(ldap_attr, '')
                if ldap_value:
                    user_data[django_field] = ldap_value
            
            # AD 사용자는 Django 비밀번호를 사용하지 않으므로 unusable password 설정
            user = User.objects.create_user(**user_data)
            user.set_unusable_password()
            user.save()
            logger.info(f"LDAP 사용자 생성: {username}")
        
        return user
    
    def get_user(self, user_id):
        """세션에서 사용자 복원 시 호출"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
