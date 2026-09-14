"""
NH선물 REST API WebSocket 클라이언트

실시간 데이터 수신을 위한 WebSocket 통신 클라이언트입니다.

실시간 API 사용 흐름:
    1. 인증 토큰 발급 (auth.get_access_token)
    2. 웹소켓 접근 키 발급 (auth.get_websocket_key)
    3. WebSocket 연결 (connect)
    4. 세션 초기화 (send_init) -> INIT_SUCCESS 확인
    5. 종목/계좌 구독 등록 (subscribe)
    6. 데이터 수신 대기 (listen) -> 콜백으로 데이터 처리
    7. 구독 해제 (unsubscribe) 후 연결 종료 (close)

핑퐁 처리:
    - 서버에서 {"code": "pingpong", "msg": "pingpong"} 메시지가 오면
      동일한 메시지를 그대로 서버로 전송하여 연결을 유지합니다.

구독/해제 헤더 코드:
    - action = "0": 세션 초기화
    - action = "A": 구독 등록
    - action = "D": 구독 해제

실시간 메시지 코드 (action_code):
    - O1: 계좌 체결
    - FA: 해외 체결 내역
    - FB: 해외 호가 내역
    - KA: 국내 주간 체결
    - KB: 국내 주간 호가
    - KC: 국내 야간 체결
    - KD: 국내 야간 호가
"""

import asyncio
import websockets
import json
import ssl


class WebSocketClient:
    """
    NH선물 실시간 API WebSocket 클라이언트

    WebSocket을 통해 실시간 체결, 호가, 계좌 체결 데이터를 수신합니다.

    속성:
        base_url (str): WebSocket URL (wss://)
        access_token (str): 인증 액세스 토큰
        ws: WebSocket 연결 객체
        running (bool): 수신 루프 실행 상태
        on_message: 메시지 수신 콜백 함수
    """

    def __init__(self, base_url: str, access_token: str):
        """
        WebSocket 클라이언트 초기화

        HTTPS URL을 WSS URL로 변환하여 WebSocket 연결에 사용합니다.

        매개변수:
            base_url (str): API 기본 URL (예: "https://apidemo.futures.co.kr")
            access_token (str): 인증 액세스 토큰 (세션 초기화에 사용)
        """
        # HTTPS를 WSS로, HTTP를 WS로 변환 (WebSocket 프로토콜)
        ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        self.base_url = ws_url
        self.access_token = access_token
        self.ws = None
        self.running = False
        self.on_message = None

    async def connect(self, access_key: str) -> bool:
        """
        WebSocket 서버에 연결

        웹소켓 접근 키를 사용하여 실시간 데이터 스트림에 연결합니다.
        연결 성공 시 HTTP 101 (Switching Protocols) 응답을 받습니다.

        매개변수:
            access_key (str): 웹소켓 접근 키 (auth.get_websocket_key로 발급)

        반환값:
            bool: 연결 성공 여부

        SSL 처리:
            truststore 패키지가 main.py에서 OS 트러스트 스토어를 주입하므로,
            ssl.create_default_context()는 자동으로 OS의 인증서를 사용합니다.
            폐쇄망 환경에서도 내부 CA 인증서가 OS에 설치되어 있으면 정상 동작합니다.
        """
        # SSL 컨텍스트 생성 (truststore가 OS 트러스트 스토어를 주입한 상태)
        ssl_context = ssl.create_default_context()

        # WebSocket 연결 URL 구성 (올바른 경로: /trade/ws-stream)
        url = f"{self.base_url}/trade/ws-stream?access_key={access_key}"

        try:
            # WebSocket 연결 수립 (자체 핑퐁을 처리하므로 websockets 기본 ping_interval은 비활성화)
            self.ws = await websockets.connect(
                url,
                ssl=ssl_context,
                ping_interval=None,
                ping_timeout=None
            )
            self.running = True
            return True
        except Exception as e:
            print(f"[오류] WebSocket 연결 실패: {e}")
            return False

    async def send_init(self) -> bool:
        """
        세션 초기화 (session_init)

        WebSocket 연결 후 세션을 초기화합니다.
        인증 토큰을 session_token로 전송하여 서버에서 세션을 인증합니다.

        반환값:
            bool: 초기화 성공 여부 (INIT_SUCCESS 수신 시 True)

        전송 메시지 형식:
            {
                "header": {"api_ver": "1", "action": "0"},
                "body": {"action_code": "session_init", "session_token": "<access_token>"}
            }

        성공 응답:
            {"code": "INIT", "msg": "INIT_SUCCESS"}
        """
        # 세션 초기화 메시지 구성
        # action = "0": 세션 초기화 헤더 코드
        init_msg = {
            "header": {
                "api_ver": "1",
                "action": "0"
            },
            "body": {
                "action_code": "session_init",
                "session_token": self.access_token
            }
        }

        # 초기화 메시지 전송
        await self.ws.send(json.dumps(init_msg))

        # 서버 응답 수신 및 확인
        response = await self.ws.recv()
        data = json.loads(response)

        # INIT_SUCCESS 여부 확인
        success = data.get("code") == "INIT" and data.get("msg") == "INIT_SUCCESS"

        if success:
            print("[성공] 세션 초기화 완료 (INIT_SUCCESS)")
        else:
            print(f"[실패] 세션 초기화 실패: {data}")

        return success

    async def subscribe(self, msg_code: str, msg_key: str | None):
        """
        실시간 데이터 구독 등록

        특정 종목 또는 계좌의 실시간 데이터 수신을 시작합니다.

        매개변수:
            msg_code (str): 메시지 코드 (O1, FA, FB, KA, KB, KC, KD)
                - O1: 계좌 체결
                - FA: 해외 체결 내역
                - FB: 해외 호가 내역
                - KA: 국내 주간 체결
                - KB: 국내 주간 호가
                - KC: 국내 야간 체결
                - KD: 국내 야간 호가
            msg_key (str): 종목코드 또는 계좌번호
                - 종목코드 예시: "A0169000" (국내), "6AU26" (해외)
                - 계좌번호 예시: "306347-11-0001" (O1 사용 시)

        전송 메시지 형식:
            action = "A" (구독 등록)
        """
        # 구독 등록 메시지 구성
        # subscribe_msg = {
        #     "header": {
        #         "api_ver": "1",
        #         "action": "A"  # A = 구독 등록
        #     },
        #     "body": {
        #         "action_code": msg_code,
        #         "action_sym": msg_key
        #     }
        # }
        body = {
            "action_code": msg_code,
        }

        # 종목코드가 필요한 채널만 action_sym 추가
        if msg_key:
            body["action_sym"] = msg_key

        subscribe_msg = {
            "header": {
                "api_ver": "1",
                "action": "A"  # A = 구독 등록
            },
            "body": body
        }

        await self.ws.send(json.dumps(subscribe_msg))

        if msg_key:
            print(f"[구독 요청] {msg_code} / {msg_key} 구독 요청 패킷 전송")
        else:
            print(f"[구독 요청] {msg_code} 구독 요청 패킷 전송")

    async def unsubscribe(self, msg_code: str, msg_key: str | None):
        """
        실시간 데이터 구독 해제

        특정 종목 또는 계좌의 실시간 데이터 수신을 중지합니다.

        매개변수:
            msg_code (str): 메시지 코드 (subscribe와 동일)
            msg_key (str): 종목코드 또는 계좌번호 (subscribe와 동일)

        전송 메시지 형식:
            action = "D" (구독 해제)
        """
        # 구독 해제 메시지 구성
        # unsubscribe_msg = {
        #     "header": {
        #         "api_ver": "1",
        #         "action": "D"  # D = 구독 해제
        #     },
        #     "body": {
        #         "action_code": msg_code,
        #         "action_sym": msg_key
        #     }
        # }
        body = {
            "action_code": msg_code,
        }
    
        # 종목코드가 필요한 채널만 action_sym 추가
        if msg_key:
            body["action_sym"] = msg_key

        unsubscribe_msg = {
            "header": {
                "api_ver": "1",
                "action": "D"  # D = 구독 해제
            },
            "body": body
        }

        await self.ws.send(json.dumps(unsubscribe_msg))

        if msg_key:
            print(f"[해제 요청] {msg_code} / {msg_key} 구독 요청 패킷 전송")
        else:
            print(f"[해제 요청] {msg_code} 구독 요청 패킷 전송")

    async def listen(self, callback):
        """
        실시간 메시지 수신 루프

        WebSocket으로부터 메시지를 지속적으로 수신하고 처리합니다.

        처리 로직:
            1. 핑퐁 메시지 수신 시: 동일 메시지를 그대로 서버에 에코 반환
            2. 일반 데이터 메시지: 콜백 함수를 통해 처리

        매개변수:
            callback: 비동기 콜백 함수 (async def callback(data: dict))
                      수신된 데이터 딕셔너리를 인자로 받음

        핑퐁 처리:
            서버에서 {"code": "pingpong", "msg": "pingpong"} 메시지가 오면
            연결 유지를 위해 동일한 메시지를 그대로 반환합니다.
        """
        self.on_message = callback

        try:
            while self.running:
                # WebSocket 메시지 수신 대기
                message = await self.ws.recv()

                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    print(f"[수신] {message}")
                    continue

                # === 핑퐁 메시지 처리 ===
                # 서버에서 핑퐁 메시지({"code": "pingpong", "msg": "pingpong"})가 오면 그대로 에코하여 연결을 유지하고 터미널에 명확히 표시
                if data.get("code") == "pingpong" or data.get("msg") == "pingpong":
                    print(f"[핑퐁 🏓] 서버 핑퐁 수신 -> 에코 전송: {message}")
                    await self.ws.send(message)
                    continue

                # === 권한/구독 오류 응답 처리 ===
                # 서버에서 code가 error/fail 이거나 에러 메시지가 포함된 응답이 올 경우 동적으로 원본 메시지 전체를 출력 후 턴 종료
                code_val = str(data.get("code", "")).lower()
                status_val = str(data.get("status", "")).lower()
                if code_val in ("error", "fail", "err") or status_val in ("error", "fail"):
                    # 서버가 보낸 실제 메시지 (msg, message, reason, desc 등 다양한 필드 대응)
                    raw_msg = data.get("msg") or data.get("message") or data.get("reason") or data.get("desc") or json.dumps(data, ensure_ascii=False)
                    print(f"\n[구독/권한 오류 ❌] 서버 실시간 오류 응답: {raw_msg}")
                    print(f"[서버 응답 전문] {json.dumps(data, ensure_ascii=False)}")
                    print("ℹ 정보: 소켓 구독이 거부되었으므로 통신을 종료하고 메뉴로 돌아갑니다.")
                    self.running = False
                    break

                # === 일반 데이터 메시지 처리 ===
                if callback:
                    await callback(data)
                else:
                    print(f"[수신 데이터] {data}")

        except websockets.ConnectionClosed as e:
            # WebSocket 연결이 종료된 경우
            print(f"\n[알림] WebSocket 연결이 종료되었습니다. (코드: {e.code}, 사유: {e.reason})")
            self.running = False
        except asyncio.CancelledError:
            # 비동기 작업이 취소된 경우 (Ctrl+C 등)
            self.running = False
        except Exception as e:
            print(f"\n[오류] WebSocket 수신 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            self.running = False

    async def close(self):
        """
        WebSocket 연결 종료

        수신 루프를 중지하고 WebSocket 연결을 안전하게 닫습니다.
        """
        self.running = False
        if self.ws:
            try:
                await self.ws.close()
                print("[알림] WebSocket 연결을 종료했습니다.")
            except Exception as e:
                print(f"[경고] WebSocket 종료 중 오류: {e}")
