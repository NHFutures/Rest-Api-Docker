"""
NH선물 REST API 인증 모듈

인증 토큰(Access Token) 발급, 폐기 및 웹소켓 접근 키 발급 기능을 제공합니다.

인증 흐름:
    1. get_access_token() -> 인증 토큰 발급 (client_credentials 방식)
    2. get_websocket_key() -> 웹소켓 접근 키 발급 (실시간 API 사용 시)
    3. revoke_token() -> 인증 토큰 폐기 (사용 완료 후)

주의사항:
    - 인증 토큰 발급을 제외한 모든 API는 유효한 Access Token이 필요합니다.
    - 토큰 유효기간은 86400초(24시간)입니다.
    - SSL 처리는 truststore 패키지를 통해 OS 트러스트 스토어를 활용합니다.
      (main.py에서 truststore.inject_into_ssl()로 주입)
"""

import requests
import json


def get_access_token(base_url: str, appkey: str, appsecret: str) -> tuple:
    """
    인증 토큰 발급

    NH선물 REST API 사용을 위한 Access Token을 발급받습니다.
    client_credentials 방식으로 APPKEY와 APPSECRET을 전송하여 인증합니다.

    매개변수:
        base_url (str): API 기본 URL (예: https://apidemo.futures.co.kr)
        appkey (str): 발급받은 APP KEY
        appsecret (str): 발급받은 APP SECRET

    반환값:
        tuple: (access_token 문자열, 전체 응답 딕셔너리)
               응답 딕셔너리에는 access_token, token_type, scopes, expires_in, expires_at 포함

    예시 응답:
        {
            "access_token": "eyJraWQ...",
            "token_type": "Bearer",
            "scopes": "S",
            "expires_in": 86400,
            "expires_at": "2026-08-07 18:42:26"
        }
    """
    # 인증 토큰 발급 엔드포인트
    url = f"{base_url}/auth-service/v1/token"

    # 요청 본문: x-www-form-urlencoded 형식으로 전송
    # 주의: 인증 토큰 발급 API는 JSON이 아닌 form-urlencoded 형식을 요구합니다.
    # requests 라이브러리에서 data= 파라미터를 사용하면
    # 자동으로 Content-Type: application/x-www-form-urlencoded 로 전송됩니다.
    form_data = {
        "appkey": appkey,
        "appsecret": appsecret,
        "grant_type": "client_credentials"
    }

    # POST 요청으로 토큰 발급 (form-urlencoded)
    # SSL 검증은 truststore가 OS 트러스트 스토어를 주입하므로 기본값(True) 사용
    response = requests.post(url, data=form_data)
    data = response.json()

    # 액세스 토큰 문자열과 전체 응답 반환
    return data.get("access_token"), data


def revoke_token(base_url: str, access_token: str, appkey: str, appsecret: str) -> dict:
    """
    인증 토큰 폐기

    발급받은 Access Token을 명시적으로 폐기합니다.

    매개변수:
        base_url (str): API 기본 URL
        access_token (str): 폐기할 액세스 토큰
        appkey (str): APP KEY
        appsecret (str): APP SECRET

    반환값:
        dict: API 응답 딕셔너리
    """
    # 토큰 폐기 엔드포인트 (Postman 사양: /v1/oauth2/token/revokeP)
    url = f"{base_url}/v1/oauth2/token/revokeP"

    # 인증 헤더에 Bearer 토큰 및 Content-Type 포함
    headers = {
        "Content-Type": "application/json;UTF-8",
        "authorization": f"Bearer {access_token}"
    }

    # 폐기 요청 본문
    body = {
        "appkey": appkey,
        "appsecret": appsecret
    }

    response = requests.post(url, headers=headers, json=body)
    return response.json()


def get_websocket_key(base_url: str, access_token: str) -> str:
    """
    웹소켓 접근 키 발급

    실시간 API(WebSocket) 사용을 위한 접근 키를 발급받습니다.
    이 키는 웹소켓 연결 URL의 access_key 파라미터로 사용됩니다.

    매개변수:
        base_url (str): API 기본 URL
        access_token (str): 유효한 액세스 토큰

    반환값:
        str: 웹소켓 접근 키 (UUID 형식, 예: "5f7b3570-26a6-44ce-9d56-0fb3c43a8fcf")

    사용 흐름:
        1. get_access_token()으로 토큰 발급
        2. get_websocket_key()로 접근 키 발급
        3. WebSocketClient에서 접근 키로 연결
    """
    # 웹소켓 접근 키 발급 엔드포인트
    url = f"{base_url}/permission/v1/web-socket-key"

    # 인증 헤더에 Bearer 토큰 포함
    headers = {
        "Content-Type": "application/json;UTF-8",
        "authorization": f"Bearer {access_token}"
    }

    # GET 요청으로 접근 키 발급
    response = requests.get(url, headers=headers)

    # 응답에서 access_key 값 추출하여 반환
    return response.json().get("access_key")
