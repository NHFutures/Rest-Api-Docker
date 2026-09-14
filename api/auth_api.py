"""
NH선물 REST API 인증 API 실행 모듈

인증 토큰 발급 및 폐기 기능을 메뉴 형태로 제공합니다.

기능:
    1. 인증토큰 발급: APPKEY/APPSECRET으로 새 토큰 발급
    2. 인증토큰 폐기: 기존 토큰 명시적 폐기
"""

from nhfs_sdk.auth import get_access_token, revoke_token
from utils.display import (
    print_menu, print_result, print_info, print_error,
    print_success, get_user_input
)
from utils.logger import log_request, log_response


def run_auth_menu(base_url: str, appkey: str, appsecret: str,
                  access_token: str, logger) -> str:
    """
    인증 API 메뉴 실행

    인증 토큰 발급 또는 폐기를 선택하여 실행합니다.

    매개변수:
        base_url (str): API 기본 URL
        appkey (str): APP KEY
        appsecret (str): APP SECRET
        access_token (str): 현재 액세스 토큰 (폐기 시 사용)
        logger: 로거 인스턴스

    반환값:
        str: 갱신된 액세스 토큰 (발급 시), 또는 기존 토큰
    """
    print_menu("인증 API를 선택하세요", [
        "인증토큰 발급",
        "인증토큰 폐기",
        "← 이전 메뉴"
    ])

    choice = get_user_input("선택")

    if choice == "1":
        # === 인증 토큰 발급 ===
        print_info("인증 토큰 발급 중...")
        logger.info("[인증] 토큰 발급 요청 (appkey: %s)", appkey[:4] + "...")

        try:
            # 토큰 발급 API 호출
            new_token, response_data = get_access_token(base_url, appkey, appsecret)

            if new_token:
                print_success("인증 토큰 발급 완료!")
                print_result("토큰 발급 응답", response_data)
                logger.info("[인증] 토큰 발급 성공 (만료: %s)", response_data.get("expires_at", ""))
                return new_token
            else:
                print_error("토큰 발급 실패")
                print_result("오류 응답", response_data)
                logger.error("[인증] 토큰 발급 실패: %s", response_data)
                return access_token

        except Exception as e:
            print_error(f"토큰 발급 중 오류 발생: {e}")
            logger.error("[인증] 토큰 발급 오류: %s", str(e))
            return access_token

    elif choice == "2":
        # === 인증 토큰 폐기 ===
        if not access_token:
            print_error("폐기할 토큰이 없습니다. 먼저 토큰을 발급하세요.")
            return access_token

        print_info("인증 토큰 폐기 중...")
        logger.info("[인증] 토큰 폐기 요청")

        try:
            # 토큰 폐기 API 호출
            response_data = revoke_token(base_url, access_token, appkey, appsecret)

            print_success("인증 토큰 폐기 완료!")
            print_result("토큰 폐기 응답", response_data)
            logger.info("[인증] 토큰 폐기 성공")

            # 폐기 후 빈 토큰 반환
            return ""

        except Exception as e:
            print_error(f"토큰 폐기 중 오류 발생: {e}")
            logger.error("[인증] 토큰 폐기 오류: %s", str(e))
            return access_token

    else:
        # 이전 메뉴로 복귀
        return access_token
