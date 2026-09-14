#!/usr/bin/env python3
"""
NH선물 REST API 파이썬 실행기

터미널 기반으로 NH선물의 REST API와 실시간 WebSocket API를 실행하고
테스트할 수 있는 프로그램입니다.

주요 기능:
    1. HTTP API 실행: 국내(주간/야간), 해외의 시세 및 계좌 API
    2. 실시간 API 실행: WebSocket을 통한 체결/호가 데이터 수신
    3. 시나리오 HTTP 실행: 시세 조회 → 주문까지 이어지는 통합 테스트
    4. 시나리오 실시간 실행: 호가+체결 결합 전광판 표시

실행 방법:
    로컬: python main.py
    도커: docker run -it --env APP_KEY=xxx --env APP_SECRET=xxx nh-open-api

SSL 처리:
    truststore 패키지를 사용하여 OS 트러스트 스토어(Windows 인증서 저장소)를 활용합니다.
    폐쇄망 환경에서 내부 CA 인증서가 OS에 설치되어 있으면 자동으로 신뢰합니다.
    verify=False 방식 대신 이 방법을 사용하여 보안성을 유지합니다.
"""

import yaml
import os
import sys
import asyncio

from render_config import ensure_config_exists

# ============================================================================
# 폐쇄망 대응: OS 트러스트 스토어 활용
# ============================================================================
# truststore 패키지를 사용하여 Python의 SSL 컨텍스트가
# OS의 인증서 저장소를 참조하도록 합니다.
#
# - Windows: Windows 인증서 저장소 사용
# - Linux: /etc/ssl/certs 등 시스템 인증서 사용
# - macOS: Keychain 사용
#
# 폐쇄망에서 내부 CA 인증서가 OS에 설치되어 있으면 자동으로 신뢰하므로
# verify=False를 사용할 필요가 없습니다.
# ============================================================================
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    print("[경고] truststore 패키지가 설치되어 있지 않습니다.")
    print("[경고] 폐쇄망 환경에서는 'pip install truststore'로 설치해주세요.")
    print("[경고] 기본 SSL 설정(certifi 번들)을 사용합니다.")
    print()

# SDK, API, 유틸리티 모듈 임포트
from nhfs_sdk.auth import get_access_token, get_websocket_key
from nhfs_sdk.rest_client import RestClient
from nhfs_sdk.ws_client import WebSocketClient
from api.domestic import (
    run_domestic_day_quote, run_domestic_day_trade,
    run_domestic_night_quote, run_domestic_night_trade
)
from api.overseas import run_overseas_quote, run_overseas_trade
from api.auth_api import run_auth_menu
from api import endpoints
from scenarios.domestic_scenario import DomesticDayScenario, DomesticNightScenario
from scenarios.overseas_scenario import OverseasScenario
from scenarios.realtime_scenario import RealtimeScenario
from utils.display import (
    print_header, print_menu, print_result, clear_screen,
    print_error, print_success, print_info, get_user_input
)
from utils.logger import setup_logger

# ============================================================================
# 전역 설정 변수
# ============================================================================
# HTTP 요청 간격 (초) - RateLimit 방지를 위해 요청 사이에 대기 시간을 둡니다.
# 이 값을 변경하면 모든 HTTP 요청의 간격이 조정됩니다.
# 서버에서 1초당 1회 제한이 있으므로 기본값은 1.0초입니다.
REQUEST_INTERVAL = 1.0


def load_config() -> dict:
    """
    설정 파일 로드 및 환경변수 적용

    config.yaml 파일을 로드하고, Docker 환경변수가 설정되어 있으면
    해당 값을 우선 적용합니다.

    환경변수 우선순위:
        1. APP_KEY / APP_SECRET -> 계좌의 appkey / appsecret 덮어쓰기
        2. ENVIRONMENT -> demo/real 자동 선택
        3. ACCOUNT_TYPE -> domestic/overseas 자동 선택

    반환값:
        dict: 설정 딕셔너리
    """
    # 설정 파일 경로 (main.py와 같은 디렉토리)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.yaml')

    if not os.path.exists(config_path):
        ensure_config_exists(
            os.path.join(base_dir, 'config.yaml.template'),
            config_path,
        )

    # YAML 설정 파일 로드
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # === 환경변수 우선 적용 (Docker 환경) ===
    # Docker 실행 시 -e APP_KEY=xxx -e APP_SECRET=xxx 로 전달 가능
    env_appkey = os.environ.get('APP_KEY', '')
    env_appsecret = os.environ.get('APP_SECRET', '')

    # 환경변수가 있으면 양쪽 계좌 모두에 적용
    if env_appkey:
        config['accounts']['domestic']['appkey'] = env_appkey
        config['accounts']['overseas']['appkey'] = env_appkey
    if env_appsecret:
        config['accounts']['domestic']['appsecret'] = env_appsecret
        config['accounts']['overseas']['appsecret'] = env_appsecret

    # 환경변수로 환경/계좌 자동 선택 (Docker 환경에서 프롬프트 없이 실행 가능)
    config['env_environment'] = os.environ.get('ENVIRONMENT', '')
    config['env_account_type'] = os.environ.get('ACCOUNT_TYPE', '')

    return config


def select_environment(config: dict) -> tuple:
    """
    실행 환경 선택 (모의투자 / 실투자)

    Docker 환경변수(ENVIRONMENT)가 설정되어 있으면 자동 선택합니다.
    없으면 터미널에서 사용자에게 프롬프트를 표시합니다.

    매개변수:
        config (dict): 설정 딕셔너리

    반환값:
        tuple: (base_url 문자열, 환경명 문자열)
    """
    # Docker 환경변수로 미리 설정된 경우 자동 선택
    env = config.get('env_environment', '')
    if env in ('demo', 'real'):
        base_url = config['urls'][env]
        env_name = "모의투자" if env == "demo" else "실투자"
        print_info(f"환경변수로 자동 선택: {env_name} ({base_url})")
        return base_url, env

    # 터미널 프롬프트로 사용자 선택
    clear_screen()
    print_header("NH선물 REST API - 환경 선택")
    print_menu("실행 환경을 선택하세요", [
        "모의투자 (apidemo.futures.co.kr)",
        "실투자 (api.futures.co.kr)"
    ])

    choice = get_user_input("선택")

    if choice == '1':
        return config['urls']['demo'], 'demo'
    elif choice == '2':
        return config['urls']['real'], 'real'
    else:
        print_error("잘못된 선택입니다. 다시 선택해주세요.")
        return select_environment(config)


def select_account(config: dict) -> tuple:
    """
    계좌 유형 선택 (국내 / 해외)

    Docker 환경변수(ACCOUNT_TYPE)가 설정되어 있으면 자동 선택합니다.
    없으면 터미널에서 사용자에게 프롬프트를 표시합니다.

    매개변수:
        config (dict): 설정 딕셔너리

    반환값:
        tuple: (계좌정보 딕셔너리, 계좌유형 문자열)
    """
    # Docker 환경변수로 미리 설정된 경우 자동 선택
    env = config.get('env_account_type', '')
    if env in ('domestic', 'overseas'):
        account = config['accounts'][env]
        acc_names = {'domestic': '국내', 'overseas': '해외'}
        acc_name = acc_names.get(env, env)
        print_info(f"환경변수로 자동 선택: {acc_name} 계좌 ({account['account_no']})")
        return account, env

    # 터미널 프롬프트로 사용자 선택
    clear_screen()
    print_header("NH선물 REST API - 계좌 선택")
    print_menu("사용할 계좌를 선택하세요", [
        f"국내 계좌 ({config['accounts']['domestic']['account_no']})",
        f"해외 계좌 ({config['accounts']['overseas']['account_no']})",
    ])

    choice = get_user_input("선택")

    if choice == '1':
        return config['accounts']['domestic'], 'domestic'
    elif choice == '2':
        return config['accounts']['overseas'], 'overseas'
    else:
        print_error("잘못된 선택입니다. 다시 선택해주세요.")
        return select_account(config)


def handle_http_menu(client, config: dict, logger, access_token: str,
                     base_url: str, appkey: str, appsecret: str) -> str:
    """
    HTTP API 메뉴 처리

    국내(주간/야간), 해외, 인증 API 실행을 위한 하위 메뉴를 관리합니다.

    매개변수:
        client: RestClient 인스턴스
        config (dict): 설정 딕셔너리
        logger: 로거 인스턴스
        access_token (str): 현재 액세스 토큰
        base_url (str): API 기본 URL
        appkey (str): APP KEY
        appsecret (str): APP SECRET

    반환값:
        str: 갱신된 액세스 토큰 (인증 메뉴에서 변경 가능)
    """
    while True:
        clear_screen()
        print_header("HTTP API 실행")
        print_menu("HTTP API 카테고리를 선택하세요", [
            "국내 (주간)",
            "국내 (야간)",
            "해외",
            "인증",
            "← 이전 메뉴"
        ])

        choice = get_user_input("선택")

        if choice == '1':
            # 국내(주간) - 시세/계좌 선택
            _handle_domestic_day(client, config, logger)
        elif choice == '2':
            # 국내(야간) - 시세/계좌 선택
            _handle_domestic_night(client, config, logger)
        elif choice == '3':
            # 해외 - 시세/계좌 선택
            _handle_overseas(client, config, logger)
        elif choice == '4':
            # 인증 - 토큰 발급/폐기
            access_token = run_auth_menu(
                base_url, appkey, appsecret, access_token, logger
            )
            # 토큰이 갱신되면 클라이언트도 업데이트
            if access_token:
                client.access_token = access_token
            get_user_input("계속하려면 Enter를 누르세요")
        elif choice == '5':
            return access_token
        else:
            print_error("잘못된 선택입니다.")
            get_user_input("계속하려면 Enter를 누르세요")

    return access_token


def _handle_domestic_day(client, config: dict, logger):
    """국내(주간) 시세/계좌 메뉴 처리"""
    clear_screen()
    print_header("국내 (주간)")
    print_menu("실행할 API를 선택하세요", [
        "시세 API",
        "계좌 API",
        "← 이전 메뉴"
    ])

    choice = get_user_input("선택")

    if choice == '1':
        run_domestic_day_quote(client, config, logger)
        get_user_input("계속하려면 Enter를 누르세요")
    elif choice == '2':
        run_domestic_day_trade(client, config, logger)
        get_user_input("계속하려면 Enter를 누르세요")


def _handle_domestic_night(client, config: dict, logger):
    """국내(야간) 시세/계좌 메뉴 처리"""
    clear_screen()
    print_header("국내 (야간)")
    print_menu("실행할 API를 선택하세요", [
        "시세 API",
        "계좌 API",
        "← 이전 메뉴"
    ])

    choice = get_user_input("선택")

    if choice == '1':
        run_domestic_night_quote(client, config, logger)
        get_user_input("계속하려면 Enter를 누르세요")
    elif choice == '2':
        run_domestic_night_trade(client, config, logger)
        get_user_input("계속하려면 Enter를 누르세요")


def _handle_overseas(client, config: dict, logger):
    """해외 시세/계좌 메뉴 처리"""
    clear_screen()
    print_header("해외")
    print_menu("실행할 API를 선택하세요", [
        "시세 API",
        "계좌 API",
        "← 이전 메뉴"
    ])

    choice = get_user_input("선택")

    if choice == '1':
        run_overseas_quote(client, config, logger)
        get_user_input("계속하려면 Enter를 누르세요")
    elif choice == '2':
        run_overseas_trade(client, config, logger)
        get_user_input("계속하려면 Enter를 누르세요")


def handle_realtime_menu(base_url: str, access_token: str, config: dict, logger):
    """
    실시간 API 메뉴 처리

    WebSocket을 통한 실시간 데이터 구독을 실행합니다.
    각 채널(O1, FA, FB, KA, KB, KC, KD) 중 하나를 선택하여 구독합니다.

    실행 흐름:
        1. 채널 선택
        2. 종목코드/계좌번호 입력
        3. 웹소켓 접근 키 발급
        4. WebSocket 연결 → 세션 초기화 → 구독
        5. 데이터 수신 및 표시
        6. Ctrl+C로 종료 → 구독 해제 → 메뉴 복귀

    매개변수:
        base_url (str): API 기본 URL
        access_token (str): 인증 액세스 토큰
        config (dict): 설정 딕셔너리
        logger: 로거 인스턴스
    """
    clear_screen()
    print_header("실시간 API 실행")
    print_menu("실시간 API를 선택하세요", [
        "계좌 체결 (O1)",
        "해외 체결 내역 (FA)",
        "해외 호가 내역 (FB)",
        "국내 주간 체결 (KA)",
        "국내 주간 호가 (KB)",
        "국내 야간 체결 (KC)",
        "국내 야간 호가 (KD)",
        "← 이전 메뉴"
    ])

    choice = get_user_input("선택")

    # 선택에 따른 메시지 코드 매핑
    code_map = {
        '1': 'O1', '2': 'FA', '3': 'FB',
        '4': 'KA', '5': 'KB', '6': 'KC', '7': 'KD'
    }

    if choice not in code_map:
        return  # 이전 메뉴 또는 잘못된 선택

    msg_code = code_map[choice]
    code_info = endpoints.REALTIME_CODES[msg_code]

    # 종목코드 또는 계좌번호 입력
    if code_info["key_type"] == "account":
        # 계좌 체결(O1)의 경우 계좌번호 입력
        account = config.get("_current_account", {})
        default_key = account.get("account_no", "")

        # O1용으로 하이픈 제거
        # default_key = default_key.replace("-", "")

        msg_key = get_user_input(f"계좌번호 입력 (기본값: {default_key})")
        if not msg_key:
            msg_key = default_key
        else:
            # 계좌번호 입력값에서 하이픈 제거
            msg_key = msg_key.replace("-", "")
    else:
    # 종목 관련 채널의 경우 종목코드 입력
        if msg_code in ('FA', 'FB'):
            default_key = config.get("symbols", {}).get("overseas", "6AU26")
        else:
            default_key = config.get("symbols", {}).get("domestic", "A0169000")
        msg_key = get_user_input(f"종목코드 입력 (기본값: {default_key})")
        if not msg_key:
            msg_key = default_key

    if msg_code == 'O1':
        msg_key = None

    print_info(f"{code_info['name']} ({msg_code}) 구독을 시작합니다...")
    # print_info(f"종목/계좌: {msg_key}")
    if msg_key:
        print_info(f"종목: {msg_key}")
    print_info("Ctrl+C로 종료하면 메인 메뉴로 돌아갑니다.")

    # 비동기 WebSocket 실행
    try:
        asyncio.run(_run_realtime_subscription(
            base_url, access_token, msg_code, msg_key, code_info['name']
        ))
    except Exception as e:
        print_error(f"실시간 실행 도중 예외가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        get_user_input("오류 확인 후 Enter 키를 누르세요")


async def _run_realtime_subscription(base_url: str, access_token: str,
                                      msg_code: str, msg_key: str | None, name: str):
    """
    실시간 데이터 구독 실행 (비동기)

    WebSocket 연결 → 세션 초기화 → 구독 → 데이터 수신의 전체 흐름을 실행합니다.
    Rate Limit 방지를 위해 각 단계 간 1초씩 슬립 대기를 줍니다.
    """
    # 1. 웹소켓 접근 키 발급 (1초 대기 후 실행)
    await asyncio.sleep(1.0)
    print_info("웹소켓 접근 키 발급 중...")
    try:
        access_key = get_websocket_key(base_url, access_token)
        if not access_key:
            print_error("웹소켓 접근 키 발급 실패")
            return
        print_success(f"웹소켓 접근 키: {access_key[:8]}...")
    except Exception as e:
        print_error(f"웹소켓 접근 키 발급 오류: {e}")
        return

    # 2. WebSocket 연결 (1초 대기 후 실행)
    await asyncio.sleep(1.0)
    print_info("WebSocket 연결 중...")
    ws_client = WebSocketClient(base_url, access_token)

    connected = await ws_client.connect(access_key)
    if not connected:
        print_error("WebSocket 연결 실패")
        return

    # 3. 세션 초기화 (1초 대기 후 실행)
    await asyncio.sleep(1.0)
    print_info("세션 초기화 중...")
    init_success = await ws_client.send_init()
    if not init_success:
        print_error("세션 초기화 실패")
        await ws_client.close()
        return

    # 4. 채널 구독 (1초 대기 후 실행)
    await asyncio.sleep(1.0)
    await ws_client.subscribe(msg_code, msg_key)
    print_info(f"{name} 구독 요청 패킷 전송 완료! 데이터 수신 대기 중...")

    # 메시지 수신 콜백
    async def on_message(data):
        """수신 데이터를 JSON 형태로 출력"""
        print_result(f"[{name}] 수신 데이터", data)

    try:
        await ws_client.listen(on_message)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print_info("\n실시간 수신을 종료합니다...")
    except Exception as e:
        print_error(f"\n실시간 통신 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        get_user_input("오류 메시지를 확인한 후 Enter 키를 누르세요")
    finally:
        try:
            await ws_client.unsubscribe(msg_code, msg_key)
        except Exception:
            pass
        await ws_client.close()
        print_success("실시간 API 종료 완료.")
        get_user_input("메뉴로 돌아가려면 Enter 키를 누르세요")


def handle_scenario_http_menu(client, config: dict, logger):
    """
    시나리오 HTTP 메뉴 처리

    시세 조회 → 주문까지 이어지는 통합 시나리오를 실행합니다.

    매개변수:
        client: RestClient 인스턴스
        config (dict): 설정 딕셔너리
        logger: 로거 인스턴스
    """
    clear_screen()
    print_header("시나리오 HTTP 실행")
    print_menu("HTTP 시나리오를 선택하세요", [
        "국내 주식 주간 시세 조회 및 주문 (지정가/시장가)",
        "국내 주식 야간 시세 조회 및 주문 (지정가/시장가)",
        "해외 주식 시세 조회 및 주문 (지정가/시장가)",
        "← 이전 메뉴"
    ])

    choice = get_user_input("선택")

    if choice == '1':
        # 국내 주간 시나리오
        scenario = DomesticDayScenario(client, config, logger)
        scenario.run_quote_and_order()
        get_user_input("계속하려면 Enter를 누르세요")
    elif choice == '2':
        # 국내 야간 시나리오
        scenario = DomesticNightScenario(client, config, logger)
        scenario.run_quote_and_order()
        get_user_input("계속하려면 Enter를 누르세요")
    elif choice == '3':
        # 해외 시나리오
        scenario = OverseasScenario(client, config, logger)
        scenario.run_quote_and_order()
        get_user_input("계속하려면 Enter를 누르세요")


def handle_scenario_realtime_menu(base_url: str, access_token: str, config: dict):
    """
    시나리오 실시간 메뉴 처리

    체결 + 호가를 결합한 전광판 시나리오를 실행합니다.

    매개변수:
        base_url (str): API 기본 URL
        access_token (str): 인증 액세스 토큰
        config (dict): 설정 딕셔너리
    """
    clear_screen()
    print_header("시나리오 실시간 실행")
    print_menu("실시간 시나리오를 선택하세요", [
        "국내주식 주간 전광판 (호가+체결 결합)",
        "국내주식 야간 전광판 (호가+체결 결합)",
        "해외주식 전광판 (호가+체결 결합)",
        "← 이전 메뉴"
    ])

    choice = get_user_input("선택")

    if choice in ('1', '2', '3'):
        # 실시간 시나리오 인스턴스 생성
        scenario = RealtimeScenario(base_url, access_token, config)

        if choice == '1':
            # 국내 주간 전광판 (KA + KB)
            asyncio.run(scenario.run_domestic_day_board())
        elif choice == '2':
            # 국내 야간 전광판 (KC + KD)
            asyncio.run(scenario.run_domestic_night_board())
        elif choice == '3':
            # 해외 전광판 (FA + FB)
            asyncio.run(scenario.run_overseas_board())


def main():
    """
    메인 함수 - 프로그램 진입점

    실행 순서:
        1. 설정 파일 로드
        2. 로거 초기화
        3. 환경 선택 (모의투자/실투자)
        4. 계좌 선택 (국내/해외)
        5. 인증 토큰 발급
        6. REST 클라이언트 생성
        7. 메인 메뉴 루프 (모든 작업 완료 후 메뉴로 복귀)
    """
    # === 1단계: 설정 로드 ===
    try:
        config = load_config()
    except FileNotFoundError:
        print("[오류] config.yaml 파일을 찾을 수 없습니다.")
        print("[안내] config.yaml.template을 config.yaml로 복사한 후 설정을 수정해주세요.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[오류] config.yaml 파싱 오류: {e}")
        sys.exit(1)

    # === 2단계: 로거 초기화 ===
    logger = setup_logger(config)
    logger.info("=" * 60)
    logger.info("NH선물 REST API 실행기 시작")
    logger.info("=" * 60)

    # === 3단계: 환경 선택 ===
    base_url, env_name = select_environment(config)
    env_display = "모의투자" if env_name == "demo" else "실투자"
    logger.info("환경 선택: %s (%s)", env_display, base_url)

    # === 4단계: 계좌 선택 ===
    account, account_type = select_account(config)
    acc_display = "국내" if account_type == "domestic" else "해외"
    logger.info("계좌 선택: %s (%s)", acc_display, account.get("account_no", ""))

    # 현재 선택된 계좌를 config에 저장 (하위 모듈에서 참조)
    config["_current_account"] = account
    config["_account_type"] = account_type

    # === 5단계: 인증 토큰 발급 ===
    appkey = account.get("appkey", "")
    appsecret = account.get("appsecret", "")

    clear_screen()
    print_header("NH선물 REST API 실행기")
    print_info(f"환경: {env_display} ({base_url})")
    print_info(f"계좌: {acc_display} ({account.get('account_no', '')})")
    print_info("인증 토큰 발급 중...")

    try:
        access_token, token_data = get_access_token(base_url, appkey, appsecret)
        if access_token:
            print_success(f"인증 토큰 발급 완료 (만료: {token_data.get('expires_at', '')})")
            logger.info("토큰 발급 성공 (만료: %s)", token_data.get("expires_at", ""))
        else:
            print_error("인증 토큰 발급 실패")
            print_result("오류 응답", token_data)
            logger.error("토큰 발급 실패: %s", token_data)
            sys.exit(1)
    except Exception as e:
        print_error(f"인증 토큰 발급 중 오류: {e}")
        logger.error("토큰 발급 오류: %s", str(e))
        sys.exit(1)

    # === 6단계: REST 클라이언트 생성 ===
    client = RestClient(
        base_url=base_url,
        access_token=access_token,
        appkey=appkey,
        appsecret=appsecret,
        request_interval=REQUEST_INTERVAL
    )

    # === 7단계: 메인 메뉴 루프 ===
    while True:
        clear_screen()
        print_header("NH선물 REST API 실행기")
        print_info(f"환경: {env_display} | 계좌: {acc_display} ({account.get('account_no', '')})")
        print_menu("실행할 작업을 선택하세요", [
            "HTTP API 실행",
            "실시간 API 실행",
            "시나리오 HTTP 실행",
            "시나리오 실시간 실행",
            "종료"
        ])

        choice = get_user_input("선택")

        if choice == '1':
            # HTTP API 메뉴 (인증 메뉴에서 토큰 갱신 가능)
            access_token = handle_http_menu(
                client, config, logger, access_token,
                base_url, appkey, appsecret
            )
            # 토큰이 갱신되었으면 클라이언트도 업데이트
            client.access_token = access_token

        elif choice == '2':
            # 실시간 API 메뉴 (WebSocket)
            handle_realtime_menu(base_url, access_token, config, logger)

        elif choice == '3':
           # 시나리오 HTTP 메뉴
           handle_scenario_http_menu(client, config, logger)

        elif choice == '4':
           # 시나리오 실시간 메뉴 (전광판)
           handle_scenario_realtime_menu(base_url, access_token, config)

        elif choice == '5':
        # elif choice == '3':
            # 종료
            print_info("프로그램을 종료합니다. 감사합니다.")
            logger.info("프로그램 정상 종료")
            break

        else:
            print_error("잘못된 선택입니다. 1~5 사이의 숫자를 입력해주세요.")
            # print_error("잘못된 선택입니다. 1~3 사이의 숫자를 입력해주세요.")
            get_user_input("계속하려면 Enter를 누르세요")


# ============================================================================
# 프로그램 진입점
# ============================================================================
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl+C로 프로그램 강제 종료 시
        print('\n\n프로그램을 종료합니다.')
        sys.exit(0)
    except Exception as e:
        # 예상치 못한 오류 발생 시 트레이스백 출력 후 사용자 입력 대기
        print(f'\n[치명적 오류 발생] {e}')
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        input("오류 메시지를 확인한 후 Enter 키를 누르면 프로그램이 종료됩니다...")
        sys.exit(1)
