"""
NH선물 REST API 국내 시나리오 모듈

Postman 사양에 맞춘 국내 선물옵션의 시세 조회 후 주문 시나리오입니다.
"""

from api import endpoints
from utils.display import (
    print_header, print_result, print_menu, print_info,
    print_error, print_success, get_user_input
)
from utils.logger import log_request, log_response


class DomesticDayScenario:
    """
    국내 주간 시세 조회 및 주문 시나리오
    """

    def __init__(self, client, config: dict, logger):
        self.client = client
        self.config = config
        self.logger = logger

    def run_quote_and_order(self):
        print_header("국내 주간 시세 조회 및 주문 시나리오")

        default_symbol = self.config.get("symbols", {}).get("domestic", "A0169000")
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})")
        if not symbol:
            symbol = default_symbol

        print_info(f"[1/2] 현재가 조회 중... (종목: {symbol})")
        quote_api = endpoints.DM_QUOTE_PRICE
        path = quote_api["path"]
        body = {"sym": symbol}

        url = f"{self.client.base_url}{path}"
        headers = self.client._get_headers()
        log_request(self.logger, "POST", url, headers, body)

        quote_data, status_code, resp_headers = self.client.post(path, body=body)
        log_response(self.logger, status_code, resp_headers, quote_data)

        if status_code != 200:
            print_error(f"시세 조회 실패 (상태: {status_code})")
            print_result("오류 응답", quote_data)
            return

        print_success("현재가 조회 완료")
        print_result("현재가 조회 결과", quote_data)

        proceed = get_user_input("주문을 진행하시겠습니까? (y/n)")
        if proceed.lower() != 'y':
            print_info("주문을 취소하고 메뉴로 돌아갑니다.")
            return

        print_menu("매수/매도를 선택하세요", ["매수", "매도"])
        sll_buy_choice = get_user_input("선택")
        trd_div = "1" if sll_buy_choice == "1" else "2"  # 1: 매수, 2: 매도

        print_menu("주문 유형을 선택하세요", ["지정가 (1)", "시장가 (2)", "조건부 (3)", "최유리 (4)"])
        nmpr_choice = get_user_input("선택 (기본값 1: 지정가)")
        ord_tp_cd = nmpr_choice if nmpr_choice in ("1", "2", "3", "4") else "1"

        ord_qty = get_user_input("주문 수량을 입력하세요 (기본값: 1)")
        if not ord_qty:
            ord_qty = "1"

        ord_pric = "0"
        if ord_tp_cd in ["1", "3"]: 
            ord_pric = get_user_input("주문 가격을 입력하세요 (기본값: 0)")
            if not ord_pric:
                ord_pric = "0"
        else:
            ord_pric = "0"  # 시장가(2), 최유리(4)일 시 0

        print_menu("체결 조건을 선택하세요", ["FAS (1)", "FOK (2)", "FAK (3)"])
        exec_cnd = get_user_input("선택")
        exec_cnd_cd = exec_cnd if exec_cnd in ("1", "2", "3") else "1"

        order_body = {
            "sym": symbol,
            "trd_div": trd_div,
            "ord_tp_cd": ord_tp_cd,
            "ord_qty": ord_qty,
            "ord_pric": ord_pric,
            "exec_cnd_cd": exec_cnd_cd
        }

        print_info("[2/2] 주문 실행 중...")
        order_api = endpoints.DM_TRADE_ORDER
        order_path = order_api["path"]

        url = f"{self.client.base_url}{order_path}"
        headers = self.client._get_headers()
        log_request(self.logger, "POST", url, headers, order_body)

        order_data, status_code, resp_headers = self.client.post(order_path, body=order_body)
        log_response(self.logger, status_code, resp_headers, order_data)

        if status_code == 200:
            print_success("주문 실행 완료!")
            print_result("주문 결과", order_data)
        else:
            print_error(f"주문 실행 실패 (상태: {status_code})")
            print_result("오류 응답", order_data)


class DomesticNightScenario:
    """
    국내 야간 시세 조회 및 주문 시나리오
    """

    def __init__(self, client, config: dict, logger):
        self.client = client
        self.config = config
        self.logger = logger

    def run_quote_and_order(self):
        print_header("국내 야간 시세 조회 및 주문 시나리오")

        default_symbol = self.config.get("symbols", {}).get("domestic", "A0169000")
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})")
        if not symbol:
            symbol = default_symbol

        print_info(f"[1/2] 야간 현재가 조회 중... (종목: {symbol})")
        quote_api = endpoints.DMN_QUOTE_PRICE
        path = quote_api["path"]
        body = {"sym": symbol}

        url = f"{self.client.base_url}{path}"
        headers = self.client._get_headers()
        log_request(self.logger, "POST", url, headers, body)

        quote_data, status_code, resp_headers = self.client.post(path, body=body)
        log_response(self.logger, status_code, resp_headers, quote_data)

        if status_code != 200:
            print_error(f"시세 조회 실패 (상태: {status_code})")
            print_result("오류 응답", quote_data)
            return

        print_success("야간 현재가 조회 완료")
        print_result("야간 현재가 조회 결과", quote_data)

        proceed = get_user_input("주문을 진행하시겠습니까? (y/n)")
        if proceed.lower() != 'y':
            print_info("주문을 취소하고 메뉴로 돌아갑니다.")
            return

        print_menu("매수/매도를 선택하세요", ["매수 (1)", "매도 (2)"])
        sll_buy_choice = get_user_input("선택")
        trd_div = "1" if sll_buy_choice == "1" else "2"  # 1: 매수, 2: 매도

        print_menu("주문 유형을 선택하세요", ["지정가 (1)", "시장가 (2)", "조건부 (3)", "최유리 (4)"])
        nmpr_choice = get_user_input("선택 (기본값 1: 지정가)")
        ord_tp_cd = nmpr_choice if nmpr_choice in ("1", "2", "3", "4") else "1"

        ord_qty = get_user_input("주문 수량을 입력하세요 (기본값: 1)")
        if not ord_qty:
            ord_qty = "1"

        ord_pric = get_user_input("주문 가격을 입력하세요 (기본값: 0)")
        if not ord_pric:
            ord_pric = "0"

        print_menu("체결 조건을 선택하세요", ["FAS (1)", "FOK (2)", "FAK (3)"])
        exec_cnd = get_user_input("선택")
        exec_cnd_cd = exec_cnd if exec_cnd in ("1", "2", "3") else "1"
                

        order_body = {
            "sym": symbol,
            "trd_div": trd_div,
            "ord_tp_cd": ord_tp_cd,
            "ord_qty": ord_qty,
            "ord_pric": ord_pric,
            "exec_cnd_cd": exec_cnd_cd
        }

        print_info("[2/2] 야간 주문 실행 중...")
        order_api = endpoints.DMN_TRADE_ORDER
        order_path = order_api["path"]

        url = f"{self.client.base_url}{order_path}"
        headers = self.client._get_headers()
        log_request(self.logger, "POST", url, headers, order_body)

        order_data, status_code, resp_headers = self.client.post(order_path, body=order_body)
        log_response(self.logger, status_code, resp_headers, order_data)

        if status_code == 200:
            print_success("야간 주문 실행 완료!")
            print_result("주문 결과", order_data)
        else:
            print_error(f"주문 실행 실패 (상태: {status_code})")
            print_result("오류 응답", order_data)
