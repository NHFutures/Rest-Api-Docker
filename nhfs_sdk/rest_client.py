"""
NH선물 REST API REST 클라이언트

HTTP REST API 호출을 위한 클라이언트 클래스입니다.
Rate Limit 방지를 위한 요청 간격 제어 기능이 내장되어 있습니다.

주요 기능:
    - GET/POST HTTP 요청 실행
    - 공통 헤더 자동 설정 (인증, Content-Type 등)
    - Rate Limit 방지를 위한 요청 간격 제어 (기본 1초)
    - 상세 로그 기록 지원
"""

import requests
import json
import time

REQUEST_INTERVAL = 1.0


class RestClient:
    """
    NH선물 REST API REST 클라이언트
    """

    def __init__(self, base_url: str, access_token: str, appkey: str,
                 appsecret: str, request_interval: float = None):
        self.base_url = base_url
        self.access_token = access_token
        self.appkey = appkey
        self.appsecret = appsecret
        self.request_interval = request_interval if request_interval is not None else REQUEST_INTERVAL
        self.last_request_time = 0

    def _get_headers(self, tr_id: str = None) -> dict:
        """
        공통 요청 헤더 생성

        Postman 명세에 맞춘 인증 및 환경 헤더 구성:
            - Content-Type: application/json;UTF-8
            - authorization: Bearer {access_token}
            - X-GW-ENV: SMUL
        """
        headers = {
            "Content-Type": "application/json;UTF-8",
            "authorization": f"Bearer {self.access_token}",
            "X-GW-ENV": "SMUL"
        }
        if self.appkey:
            headers["appkey"] = self.appkey
        if self.appsecret:
            headers["appsecret"] = self.appsecret
        if tr_id:
            headers["tr_id"] = tr_id
        return headers

    def _rate_limit(self):
        """Rate Limit 제어"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            wait_time = self.request_interval - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def get(self, path: str, tr_id: str = None, params: dict = None) -> tuple:
        """GET 요청 실행"""
        self._rate_limit()
        url = f"{self.base_url}{path}"
        headers = self._get_headers(tr_id)
        response = requests.get(url, headers=headers, params=params)
        try:
            res_json = response.json()
        except Exception:
            res_json = {"raw_text": response.text}
        return res_json, response.status_code, dict(response.headers)

    def post(self, path: str, tr_id: str = None, body: dict = None) -> tuple:
        """POST 요청 실행"""
        self._rate_limit()
        url = f"{self.base_url}{path}"
        headers = self._get_headers(tr_id)
        response = requests.post(url, headers=headers, json=body if body is not None else {})
        try:
            res_json = response.json()
        except Exception:
            res_json = {"raw_text": response.text}
        return res_json, response.status_code, dict(response.headers)
