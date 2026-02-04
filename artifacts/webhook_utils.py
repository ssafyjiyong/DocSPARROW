"""
Discord 웹훅 전송 유틸리티
"""
import requests
import logging
from django.utils import timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def create_embed_message(event_type: str, data: Dict[str, Any]) -> str:
    """
    이벤트 타입에 따라 Discord 메시지 생성 (코드블럭 형식)
    
    Args:
        event_type: 이벤트 타입 ('file_upload', 'file_delete', 'download_single', 'download_bulk', 'admin_activity')
        data: 이벤트 데이터
    
    Returns:
        Discord 메시지 문자열
    """
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if event_type == 'file_upload':
        message = f"""```
[파일 업로드] {data.get('filename')}
업로더     : {data.get('uploader', 'Unknown')}
제품       : {data.get('product', 'N/A')}
카테고리   : {data.get('category', 'N/A')}
버전       : {data.get('version', 'N/A')}
언어       : {data.get('country', 'Global')}
시간       : {timestamp}
```"""
    
    elif event_type == 'file_delete':
        message = f"""```
[파일 삭제] {data.get('filename')}
삭제자     : {data.get('deleter', 'Unknown')}
제품       : {data.get('product', 'N/A')}
카테고리   : {data.get('category', 'N/A')}
버전       : {data.get('version', 'N/A')}
언어       : {data.get('country', 'Global')}
시간       : {timestamp}
```"""
    
    elif event_type == 'download_single':
        message = f"""```
[개별 다운로드] {data.get('filename')}
사용자     : {data.get('downloader', 'Unknown')}
제품       : {data.get('product', 'N/A')}
카테고리   : {data.get('category', 'N/A')}
버전       : {data.get('version', 'N/A')}
시간       : {timestamp}
```"""
    
    elif event_type == 'download_bulk':
        message = f"""```
[일괄 다운로드] {data.get('product')}
사용자     : {data.get('downloader', 'Unknown')}
제품       : {data.get('product', 'N/A')}
언어       : {data.get('country', 'Global')}
파일 수    : {data.get('file_count', 0)}
시간       : {timestamp}
```"""
    
    elif event_type == 'admin_activity':
        message = f"""```
[관리자 활동] {data.get('activity', 'Unknown')}
관리자     : {data.get('admin', 'Unknown')}
상세       : {data.get('details', 'N/A')}
시간       : {timestamp}
```"""
    
    else:
        message = f"```\n[알 수 없는 이벤트]\n시간       : {timestamp}\n```"
    
    return message



def send_discord_webhook(webhook_url: str, message: str) -> bool:
    """
    Discord 웹훅으로 메시지 전송
    
    Args:
        webhook_url: Discord 웹훅 URL
        message: 전송할 메시지 문자열
    
    Returns:
        성공 여부
    """
    try:
        payload = {
            "content": message,
            "username": "DocSPARROW"
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=5
        )
        
        if response.status_code in [200, 204]:
            logger.info(f"웹훅 전송 성공: {webhook_url[:50]}...")
            return True
        else:
            logger.error(f"웹훅 전송 실패 (상태 코드 {response.status_code}): {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"웹훅 전송 타임아웃: {webhook_url[:50]}...")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"웹훅 전송 오류: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"웹훅 전송 예외: {str(e)}")
        return False


def trigger_webhooks(event_type: str, event_data: Dict[str, Any]) -> None:
    """
    활성화된 웹훅들에게 이벤트 전송
    
    Args:
        event_type: 이벤트 타입
        event_data: 이벤트 데이터
    """
    from .models import Webhook
    
    try:
        # 이벤트 타입에 따라 필터링
        event_field_map = {
            'file_upload': 'event_file_upload',
            'file_delete': 'event_file_delete',
            'download_single': 'event_download_single',
            'download_bulk': 'event_download_bulk',
            'admin_activity': 'event_admin_activity',
        }
        
        event_field = event_field_map.get(event_type)
        if not event_field:
            logger.warning(f"알 수 없는 이벤트 타입: {event_type}")
            return
        
        # 활성화되고 해당 이벤트를 구독하는 웹훅 조회
        filter_kwargs = {
            'is_active': True,
            event_field: True
        }
        webhooks = Webhook.objects.filter(**filter_kwargs)
        
        if not webhooks.exists():
            logger.debug(f"이벤트 {event_type}에 대한 활성화된 웹훅 없음")
            return
        
        # 메시지 생성
        message = create_embed_message(event_type, event_data)
        
        # 각 웹훅에 전송
        for webhook in webhooks:
            send_discord_webhook(webhook.webhook_url, message)
            
    except Exception as e:
        logger.error(f"웹훅 트리거 오류: {str(e)}")
        # 웹훅 전송 실패가 원래 작업에 영향을 주지 않도록 예외를 삼킴
