"""
NH선물 REST API 엔드포인트 정의

Postman 컬렉션 및 전체_API_문서.xlsx 명세 기반의
실제 API URL 경로, HTTP 메서드, TR코드 포함 명칭을 제공합니다.
"""

# ============================================================================
# 인증 API
# ============================================================================
AUTH_TOKEN = {
    "path": "/auth-service/v1/token",
    "method": "POST",
    "name": "접근토큰 발급 (/auth-service/v1/token)"
}
AUTH_REVOKE = {
    "path": "/v1/oauth2/token/revokeP",
    "method": "POST",
    "name": "접근토큰 폐기 (/v1/oauth2/token/revokeP)"
}
WS_KEY = {
    "path": "/permission/v1/web-socket-key",
    "method": "GET",
    "name": "웹소켓 접근키 발급 (/permission/v1/web-socket-key)"
}

# ============================================================================
# 국내(주간) 시세 API - /trade/v1/domestic/
# ============================================================================
DM_QUOTE_PRICE = {
    "path": "/trade/v1/domestic/price",
    "method": "POST",
    "name": "국내 현재가 (SDIF7021Q01)"
}
DM_QUOTE_ASKING = {
    "path": "/trade/v1/domestic/price-bid",
    "method": "POST",
    "name": "국내 호가 (SDIFPIBOQ01)"
}
DM_QUOTE_DAILY = {
    "path": "/trade/v1/domestic/chart-daily",
    "method": "POST",
    "name": "국내 차트(일) (SDIF7201Q03)"
}
DM_QUOTE_MINUTE = {
    "path": "/trade/v1/domestic/chart-minute",
    "method": "POST",
    "name": "국내 차트(분) (SDIF7201Q02)"
}
DM_QUOTE_FUTURES_ALL = {
    "path": "/trade/v1/domestic/price-all-futures",
    "method": "POST",
    "name": "국내 선물 전체 시세 (SDIF7023Q01)"
}
DM_QUOTE_OPTION_ALL = {
    "path": "/trade/v1/domestic/price-all-option",
    "method": "POST",
    "name": "국내 옵션 전체 시세 (SDIF7057Q03)"
}
DM_QUOTE_INVESTOR = {
    "path": "/trade/v1/domestic/trend-investor",
    "method": "POST",
    "name": "국내 투자자 직전 매매동향 (SDIF7172Q01)"
}
DM_QUOTE_EXPECT = {
    "path": "/trade/v1/domestic/price-expect-fill",
    "method": "POST",
    "name": "국내 종목별 예상 체결가 (SDIF7021Q06)"
}
DM_QUOTE_PRODUCT = {
    "path": "/trade/v1/domestic/product-detail",
    "method": "POST",
    "name": "국내 품목별 세부정보 (SDBS9003Q01)"
}

# ============================================================================
# 국내(야간) 시세 API - /trade/v1/domestic/
# ============================================================================
DMN_QUOTE_PRICE = {
    "path": "/trade/v1/domestic/price-night",
    "method": "POST",
    "name": "국내 야간 현재가 (SDIF7223Q01)"
}
DMN_QUOTE_OPTION_ALL = {
    "path": "/trade/v1/domestic/price-all-option-night",
    "method": "POST",
    "name": "국내 야간 옵션 전체 시세 (SDIF7224Q02)"
}

# ============================================================================
# 국내(주간) 계좌 API - /trade/v1/domestic/
# ============================================================================
DM_TRADE_ORDER = {
    "path": "/trade/v1/domestic/order",
    "method": "POST",
    "name": "국내 신규주문 (SDBS1231U01)"
}
DM_TRADE_MODIFY = {
    "path": "/trade/v1/domestic/modify",
    "method": "POST",
    "name": "국내 정정주문 (SDBS1231U02)"
}
DM_TRADE_CANCEL = {
    "path": "/trade/v1/domestic/cancel",
    "method": "POST",
    "name": "국내 취소주문 (SDBS1231U03)"
}
DM_TRADE_QTY = {
    "path": "/trade/v1/domestic/orderable-quantity",
    "method": "POST",
    "name": "국내 주문가능수량 (SDBS1261Q01)"
}
DM_TRADE_BALANCE = {
    "path": "/trade/v1/domestic/open-interest",
    "method": "POST",
    "name": "국내 잔고내역 (SDBS3085Q01)"
}
DM_TRADE_ERRORS = {
    "path": "/trade/v1/domestic/order-error",
    "method": "POST",
    "name": "국내 주문오류내역 (SDBS3068Q01)"
}
DM_TRADE_ORDER_HISTORY = {
    "path": "/trade/v1/domestic/order-history",
    "method": "POST",
    "name": "국내 주문내역 (SDBS3066Q01)"
}
DM_TRADE_DEPOSIT = {
    "path": "/trade/v1/domestic/deposit",
    "method": "POST",
    "name": "국내 예수금 조회 (SDBS5001Q01)"
}

# ============================================================================
# 국내(야간) 계좌 API - /trade/v1/domestic/
# ============================================================================
DMN_TRADE_ORDER = {
    "path": "/trade/v1/domestic/order-night",
    "method": "POST",
    "name": "국내 야간 신규 주문 (SDBS1234U01)"
}
DMN_TRADE_MODIFY = {
    "path": "/trade/v1/domestic/modify-night",
    "method": "POST",
    "name": "국내 야간 정정 주문 (SDBS1234U02)"
}
DMN_TRADE_CANCEL = {
    "path": "/trade/v1/domestic/cancel-night",
    "method": "POST",
    "name": "국내 야간 취소 주문 (SDBS1234U03)"
}

# ============================================================================
# 해외 시세 API - /trade/v1/overseas/
# ============================================================================
OS_QUOTE_PRICE = {
    "path": "/trade/v1/overseas/price",
    "method": "POST",
    "name": "해외 현재가 (PIBO7011D)"
}
OS_QUOTE_ASKING = {
    "path": "/trade/v1/overseas/bid-price",
    "method": "POST",
    "name": "해외 호가 (PIBO7012)"
}
OS_QUOTE_DAILY = {
    "path": "/trade/v1/overseas/chart-daily",
    "method": "POST",
    "name": "해외 차트(일) (PIBO7503)"
}
OS_QUOTE_WEEK_MONTH = {
    "path": "/trade/v1/overseas/chart-week-month",
    "method": "POST",
    "name": "해외 차트(주/월) (PIBO7504)"
}
OS_QUOTE_MINUTE = {
    "path": "/trade/v1/overseas/chart-minute",
    "method": "POST",
    "name": "해외 차트(분) (PIBO7502)"
}
OS_QUOTE_FUTURES_ALL = {
    "path": "/trade/v1/overseas/price-all-futures",
    "method": "POST",
    "name": "해외 선물전체시세 (PIBO7011)"
}
OS_QUOTE_OPTION_ALL = {
    "path": "/trade/v1/overseas/price-all-option",
    "method": "POST",
    "name": "해외 옵션전체시세 (PIBO7051)"
}
OS_QUOTE_PRODUCT = {
    "path": "/trade/v1/overseas/product-detail",
    "method": "POST",
    "name": "해외 품목별 세부정보 (SGBS7108Q01)"
}
OS_QUOTE_OPERATIONS = {
    "path": "/trade/v1/overseas/market-operations",
    "method": "POST",
    "name": "해외 장운영정보 (SGBS7108Q02)"
}


# ============================================================================
# 해외 계좌 API - /trade/v1/overseas/
# ============================================================================
OS_TRADE_ORDER = {
    "path": "/trade/v1/overseas/order",
    "method": "POST",
    "name": "해외 주문 (SGBS3500U03)"
}
OS_TRADE_QTY = {
    "path": "/trade/v1/overseas/orderable-quantity",
    "method": "POST",
    "name": "해외 주문가능수량 (SGBS3500Q07)"
}
OS_TRADE_ORDER_HISTORY = {
    "path": "/trade/v1/overseas/order-history",
    "method": "POST",
    "name": "해외 주문내역 (SGBS9001Q01)"
}
OS_TRADE_BALANCE = {
    "path": "/trade/v1/overseas/open-interest",
    "method": "POST",
    "name": "해외 잔고내역 (SGBS9001Q03)"
}
OS_TRADE_ORDERS = {
    "path": "/trade/v1/overseas/order-open",
    "method": "POST",
    "name": "해외 미체결내역 (SGBS9001Q01)"
}
OS_TRADE_ORDERS_DETAIL = {
    "path": "/trade/v1/overseas/order-open-detail",
    "method": "POST",
    "name": "해외 미체결내역 상세 (SGBS3520Q01)"
}
OS_TRADE_ERROR = {
    "path": "/trade/v1/overseas/order-error",
    "method": "POST",
    "name": "해외 주문오류내역 (SGBS3534Q01)"
}
OS_TRADE_SETTLEMENT = {
    "path": "/trade/v1/overseas/price-settlement",
    "method": "POST",
    "name": "해외 정산가 조회 (SGBS7109Q01)"
}
OS_TRADE_DEPOSIT = {
    "path": "/trade/v1/overseas/deposit",
    "method": "POST",
    "name": "해외 예수금 조회 (SGBS3205Q01)"
}
OS_TRADE_EXPIRY = {
    "path": "/trade/v1/overseas/product-expiry",
    "method": "POST",
    "name": "해외 만기일 조회 (SGBS3577Q01)"
}
OS_TRADE_CUMULATIVE_PL = {
    "path": "/trade/v1/overseas/cumulative-pl",
    "method": "POST",
    "name": "해외 누적 손익현황 (SGBS5502Q01)"
}
OS_TRADE_EXPIRY_STATUS = {
    "path": "/trade/v1/overseas/open-interest-expiry",
    "method": "POST",
    "name": "해외 보유포지션만기조회 (SGBS3554Q01)"
}

# ============================================================================
# 메뉴 그룹 정의
# ============================================================================
DM_QUOTE_APIS = [
    DM_QUOTE_PRICE, DM_QUOTE_ASKING, DM_QUOTE_DAILY,
    DM_QUOTE_MINUTE, DM_QUOTE_FUTURES_ALL, DM_QUOTE_OPTION_ALL,
    DM_QUOTE_INVESTOR, DM_QUOTE_EXPECT, DM_QUOTE_PRODUCT
]
DM_TRADE_APIS = [
    DM_TRADE_ORDER, DM_TRADE_MODIFY, DM_TRADE_CANCEL, DM_TRADE_QTY,
    DM_TRADE_BALANCE, DM_TRADE_ERRORS, DM_TRADE_ORDER_HISTORY, DM_TRADE_DEPOSIT 
]

DMN_QUOTE_APIS = [
    DMN_QUOTE_PRICE, DMN_QUOTE_OPTION_ALL
]
DMN_TRADE_APIS = [
    DMN_TRADE_ORDER, DMN_TRADE_MODIFY, DMN_TRADE_CANCEL
]

OS_QUOTE_APIS = [
    OS_QUOTE_PRICE, OS_QUOTE_ASKING, OS_QUOTE_DAILY, 
    OS_QUOTE_MINUTE, OS_QUOTE_OPTION_ALL,
    OS_QUOTE_PRODUCT, OS_QUOTE_OPERATIONS
]
OS_TRADE_APIS = [
    OS_TRADE_ORDER, OS_TRADE_QTY, OS_TRADE_ERROR,
    OS_TRADE_ORDER_HISTORY, OS_TRADE_BALANCE,
    OS_TRADE_DEPOSIT, OS_TRADE_EXPIRY, OS_TRADE_EXPIRY_STATUS, OS_TRADE_CUMULATIVE_PL
]

# 실시간 API 코드 정의
REALTIME_CODES = {
    "O1": {"name": "계좌 체결 (O1)", "key_type": "account"},
    "FA": {"name": "해외 체결 내역 (FA)", "key_type": "symbol"},
    "FB": {"name": "해외 호가 내역 (FB)", "key_type": "symbol"},
    "KA": {"name": "국내 주간 체결 (KA)", "key_type": "symbol"},
    "KB": {"name": "국내 주간 호가 (KB)", "key_type": "symbol"},
    "KC": {"name": "국내 야간 체결 (KC)", "key_type": "symbol"},
    "KD": {"name": "국내 야간 호가 (KD)", "key_type": "symbol"},
}
