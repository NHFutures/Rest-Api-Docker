"""
NH선물 REST API 실시간 전광판 시나리오 모듈

HTTP 사전 조회로 초기 시세/호가를 짠 맞춘 후, WebSocket 실시간 체결/호가 패킷으로 
수치들을 덮어씌워(Overlay) 스크롤 밀림 없이 제자리에 고정 갱신되는 전광판을 제공합니다.
"""

import asyncio
import json
from rich.live import Live
from nhfs_sdk.auth import get_websocket_key
from nhfs_sdk.rest_client import RestClient
from nhfs_sdk.ws_client import WebSocketClient
from utils.display import (
    print_header, print_info, print_error, print_success,
    make_ticker_group, get_user_input, clear_screen
)


class RealtimeScenario:
    """
    실시간 전광판 시나리오 클래스
    """

    def __init__(self, base_url: str, access_token: str, config: dict):
        self.base_url = base_url
        self.access_token = access_token
        self.config = config
        self.execution_data = {}
        self.quote_data = {}

    def _unpack_body(self, data):
        """
        국내/해외 HTTP 및 WebSocket 응답에서 하위 객체(Outbound, OutRec, output, Occurs1 등)를 언패킹
        """
        if isinstance(data, dict):
            # 하위 객체 필드 자동 탐색
            for k in ("Outbound", "OutRec", "output", "Occurs1", "occurs1", "Iccurs1"):
                if k in data:
                    node = data[k]
                    if isinstance(node, dict):
                        return node
                    elif isinstance(node, list) and len(node) > 0 and isinstance(node[0], dict):
                        return node[0]
        return data if isinstance(data, dict) else {}

    def _fetch_initial_data(self, market_type: str, symbol: str, exch_cd: str = ""):
        """
        국내/해외 공통 HTTP API를 통한 초기 시세 및 호가 데이터 사전 맞춤
        """
        print_info(f"[{market_type}] 초기 시세 및 호가 데이터 HTTP 조회 중... (종목: {symbol})")
        account = self.config.get("_current_account", {})
        client = RestClient(
            base_url=self.base_url,
            access_token=self.access_token,
            appkey=account.get("appkey", ""),
            appsecret=account.get("appsecret", ""),
            request_interval=0.5
        )

        try:
            if "해외" in market_type:
                # 해외 시세 및 호가 HTTP 호출
                price_res, _, _ = client.post(
                    "/trade/v1/overseas/price",
                    body={"Iccurs1": {"iccurs1_exch_cd": exch_cd, "iccurs1_sym": symbol}}
                )
                bid_res, _, _ = client.post(
                    "/trade/v1/overseas/bid-price",
                    body={"exch_cd": exch_cd, "sym": symbol}
                )
                self.execution_data.update(self._unpack_body(price_res))
                self.quote_data.update(self._unpack_body(bid_res))
            else:
                # 국내 주간/야간 시세 및 호가 HTTP 호출 (필드 구조 동일 처리)
                path_price = "/trade/v1/domestic/price-night" if "야간" in market_type else "/trade/v1/domestic/price"
                price_res, _, _ = client.post(path_price, body={"Series": symbol})
                bid_res, _, _ = client.post("/trade/v1/domestic/price-bid", body={"exch_cd": exch_cd, "sym": symbol})

                self.execution_data.update(self._unpack_body(price_res))
                self.quote_data.update(self._unpack_body(bid_res))

            print_success("초기 HTTP 시세/호가 동기화 완료!")

        except Exception as e:
            print_info(f"초기 HTTP 시세 조회 예외 (WebSocket 수신으로 계속 진행): {e}")

    async def _run_board(self, exec_code: str, quote_code: str,
                         msg_key: str, market_type: str, exch_cd: str = ""):
        """
        Rich Live 기반 고정 갱신 실시간 전광판 (국내/해외 필드 동일 처리)
        """
        print_header(f"{market_type} 실시간 전광판")

        # 1. HTTP API로 초기 시세/호가 사전 동기화
        self._fetch_initial_data(market_type, msg_key, exch_cd)

        # 2. 웹소켓 접근 키 발급 (1초 대기)
        await asyncio.sleep(1.0)
        print_info("웹소켓 접근 키 발급 중...")
        try:
            access_key = get_websocket_key(self.base_url, self.access_token)
            if not access_key:
                print_error("웹소켓 접근 키 발급 실패")
                return
            print_success(f"웹소켓 접근 키 발급 완료: {access_key[:8]}...")
        except Exception as e:
            print_error(f"웹소켓 접근 키 발급 오류: {e}")
            return

        # 3. WebSocket 연결 (1초 대기)
        await asyncio.sleep(1.0)
        print_info("WebSocket 연결 중...")
        ws_client = WebSocketClient(self.base_url, self.access_token)

        connected = await ws_client.connect(access_key)
        if not connected:
            print_error("WebSocket 연결 실패")
            return
        print_success("WebSocket 연결 성공")

        # 4. 세션 초기화 (1초 대기)
        await asyncio.sleep(1.0)
        print_info("세션 초기화 중...")
        init_success = await ws_client.send_init()
        if not init_success:
            print_error("세션 초기화 실패")
            await ws_client.close()
            return

        # 5. 채널 구독 요청 (1초 대기)
        await asyncio.sleep(1.0)
        print_info(f"채널 구독 요청 중... (체결: {exec_code}, 호가: {quote_code}, 종목: {msg_key})")
        await ws_client.subscribe(exec_code, msg_key)
        await asyncio.sleep(1.0)
        await ws_client.subscribe(quote_code, msg_key)
        print_info("채널 구독 요청 패킷 전송 완료! 전광판 화면을 시작합니다...")
        await asyncio.sleep(1.0)

        # === 6. Rich Live 화면 시작 (제자리 고정 갱신) ===
        clear_screen()
        
        with Live(make_ticker_group(self.execution_data, self.quote_data, market_type, msg_key, "연결 대기 중..."), refresh_per_second=4) as live:
            
            async def on_message(data):
                body = self._unpack_body(data.get("body", data))

                hdr = data.get("header", {})
                msg_code = hdr.get("msg_code") or hdr.get("action_code") or body.get("type", "")

                # 호가 데이터 덮어쓰기 (국내/해외 동일 파싱: pask1, askp1, pbid1, bidp1 등)
                if msg_code in (quote_code, "FB", "KB", "KD") or any(k in body for k in ("pask1", "askp1", "pbid1", "bidp1", "vask1", "vbid1", "askp_rsqn1", "bidp_rsqn1")):
                    if isinstance(body, dict):
                        self.quote_data.update(body)

                # 체결/현재가 데이터 덮어쓰기 (국내/해외 동일 파싱: last, clast, NowPrc, price, stck_prpr 등)
                if msg_code in (exec_code, "FA", "KA", "KC", "O1") or any(k in body for k in ("last", "clast", "NowPrc", "stck_prpr", "price", "tvol", "cvol")):
                    if isinstance(body, dict):
                        self.execution_data.update(body)

                # Live 화면 고정 갱신
                live.update(make_ticker_group(self.execution_data, self.quote_data, market_type, msg_key, "실시간 수신 중..."))

            try:
                await ws_client.listen(on_message)
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            except Exception as e:
                live.update(make_ticker_group(self.execution_data, self.quote_data, market_type, msg_key, f"오류: {e}"))
            finally:
                try:
                    await ws_client.unsubscribe(exec_code, msg_key)
                    await ws_client.unsubscribe(quote_code, msg_key)
                except Exception:
                    pass
                await ws_client.close()

        print_success("전광판 라이브 화면 종료.")
        get_user_input("메인 메뉴로 돌아가려면 Enter 키를 누르세요")

    async def run_domestic_day_board(self):
        default_symbol = self.config.get("symbols", {}).get("domestic", "A0169000")
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})")
        if not symbol:
            symbol = default_symbol
        await self._run_board("KA", "KB", symbol, "국내주간")

    async def run_domestic_night_board(self):
        default_symbol = self.config.get("symbols", {}).get("domestic", "A0169000")
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})")
        if not symbol:
            symbol = default_symbol
        await self._run_board("KC", "KD", symbol, "국내야간")

    async def run_overseas_board(self):
        default_exch_cd = "FCME"
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch_cd})") or default_exch_cd

        default_symbol = self.config.get("symbols", {}).get("overseas", "6AU26")
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})")
        if not symbol:
            symbol = default_symbol
        await self._run_board("FA", "FB", symbol, "해외", exch_cd)
