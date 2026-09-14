"""
NH선물 REST API 로깅 모듈

HTTP 요청/응답을 상세하게 기록하는 로깅 기능을 제공합니다.
파일과 콘솔에 동시에 로그를 출력합니다.

보안 기능:
    - 민감한 정보(appsecret, authorization 토큰)를 마스킹 처리합니다.
    - 예: "LzEm7l1J...Mlkg" (앞 8자 + ... + 뒤 4자)
"""

import logging
import os
import json
import copy


def _mask_sensitive(value: str, show_chars: int = 4) -> str:
    """
    민감한 데이터 마스킹 처리

    보안을 위해 API 키, 토큰 등 민감한 문자열의 중간 부분을 마스킹합니다.

    매개변수:
        value (str): 마스킹할 문자열
        show_chars (int): 앞/뒤에 보여줄 문자 수 (기본 4자)

    반환값:
        str: 마스킹된 문자열 (예: "LzEm...Mlkg")
    """
    if not value or len(value) <= show_chars * 2:
        return "****"
    return f"{value[:show_chars]}...{value[-show_chars:]}"


def _mask_headers(headers: dict) -> dict:
    """
    HTTP 헤더에서 민감한 정보 마스킹

    로그 기록 시 보안 관련 헤더 값을 마스킹 처리합니다.

    마스킹 대상:
        - appsecret: APP SECRET 키
        - authorization: Bearer 토큰

    매개변수:
        headers (dict): 원본 HTTP 헤더

    반환값:
        dict: 마스킹 처리된 헤더 (원본은 변경하지 않음)
    """
    # 원본 헤더를 변경하지 않기 위해 복사
    masked = copy.deepcopy(headers)

    # appsecret 마스킹
    if "appsecret" in masked:
        masked["appsecret"] = _mask_sensitive(masked["appsecret"])

    # authorization 토큰 마스킹 (Bearer 접두사 유지)
    if "authorization" in masked:
        auth_value = masked["authorization"]
        if auth_value.startswith("Bearer "):
            token = auth_value[7:]  # "Bearer " 이후 토큰 부분
            masked["authorization"] = f"Bearer {_mask_sensitive(token, 8)}"

    return masked


def setup_logger(config: dict) -> logging.Logger:
    """
    로거 설정 및 초기화

    파일 핸들러와 콘솔 핸들러를 모두 설정하여
    로그를 파일과 터미널에 동시에 출력합니다.

    매개변수:
        config (dict): 로깅 설정 딕셔너리
            - level (str): 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
            - file (str): 로그 파일 경로 (예: "logs/api_runner.log")
            - format (str): 로그 포맷 문자열

    반환값:
        logging.Logger: 설정된 로거 인스턴스
    """
    # 로깅 설정 추출 (기본값 포함)
    log_config = config.get("logging", {})
    log_level = getattr(logging, log_config.get("level", "DEBUG").upper(), logging.DEBUG)
    log_file = log_config.get("file", "logs/api_runner.log")
    log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 로그 파일 디렉토리 생성 (존재하지 않으면)
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 로거 인스턴스 생성
    logger = logging.getLogger("nh_open_api")
    logger.setLevel(log_level)

    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()

    # 포맷터 생성
    formatter = logging.Formatter(log_format)

    # === 파일 핸들러: 로그 파일에 기록 ===
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # === 콘솔 핸들러: 터미널에 출력 ===
    # 콘솔에는 INFO 이상만 출력하여 가독성 유지
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("로거 초기화 완료 (파일: %s, 레벨: %s)", log_file, log_config.get("level", "DEBUG"))

    return logger


def log_request(logger: logging.Logger, method: str, url: str,
                headers: dict, body=None):
    """
    HTTP 요청 상세 로그 기록

    API 호출 시 요청 정보를 상세하게 기록합니다.
    민감한 헤더 정보는 자동으로 마스킹 처리됩니다.

    매개변수:
        logger (logging.Logger): 로거 인스턴스
        method (str): HTTP 메서드 (GET, POST)
        url (str): 요청 URL
        headers (dict): 요청 헤더
        body: 요청 본문 (dict 또는 None)
    """
    # 헤더에서 민감한 정보 마스킹
    masked_headers = _mask_headers(headers)

    logger.debug("=" * 60)
    logger.debug("[HTTP 요청] %s %s", method, url)
    logger.debug("[요청 헤더] %s", json.dumps(masked_headers, ensure_ascii=False, indent=2))

    if body:
        logger.debug("[요청 본문] %s", json.dumps(body, ensure_ascii=False, indent=2))

    logger.debug("-" * 60)


def log_response(logger: logging.Logger, status_code: int,
                 headers: dict, body):
    """
    HTTP 응답 상세 로그 기록

    API 응답 결과를 상세하게 기록합니다.

    매개변수:
        logger (logging.Logger): 로거 인스턴스
        status_code (int): HTTP 상태 코드 (200, 400, 500 등)
        headers (dict): 응답 헤더
        body: 응답 본문 (dict)
    """
    # 상태 코드에 따른 로그 레벨 결정
    if status_code >= 400:
        log_func = logger.error
    else:
        log_func = logger.debug

    log_func("[HTTP 응답] 상태 코드: %d", status_code)
    log_func("[응답 헤더] %s", json.dumps(dict(headers), ensure_ascii=False, indent=2)
             if isinstance(headers, dict) else str(headers))
    log_func("[응답 본문] %s", json.dumps(body, ensure_ascii=False, indent=2)
             if isinstance(body, dict) else str(body))
    log_func("=" * 60)
