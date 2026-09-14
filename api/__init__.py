"""
NH선물 REST API 모듈 패키지

각 시장별 API 실행 및 엔드포인트 정의를 제공합니다.

모듈 구성:
    - endpoints: 모든 API 엔드포인트 및 거래ID(tr_id) 상수 정의
    - domestic: 국내(주간/야간) 시세 및 계좌 API 실행
    - overseas: 해외 시세 및 계좌 API 실행
    - auth_api: 인증 토큰 발급/폐기 API 실행
"""
