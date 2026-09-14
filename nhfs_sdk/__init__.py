"""
NH선물 REST API SDK 패키지

이 패키지는 NH선물 REST API와 통신하기 위한 핵심 모듈을 제공합니다.

모듈 구성:
    - auth: 인증 토큰 발급/폐기, 웹소켓 접근 키 발급
    - rest_client: REST API 호출 클라이언트 (Rate Limit 지원)
    - ws_client: WebSocket 실시간 통신 클라이언트 (핑퐁, 구독/해제)
"""
