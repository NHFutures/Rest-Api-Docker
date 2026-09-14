"""
NH선물 REST API 해외 시나리오 모듈

Postman 사양에 맞춘 해외 선물옵션의 시세 조회 후 주문 시나리오입니다.
"""

from api import endpoints
from utils.display import (
    print_header, print_result, print_menu, print_info,
    print_error, print_success, get_user_input
)
from utils.logger import log_request, log_response


class OverseasScenario:
    """
    해외 시세 조회 및 주문 시나리오
    """

    def __init__(self, client, config: dict, logger):
        self.client = client
        self.config = config
        self.logger = logger

    def run_quote_and_order(self):
        print_header("해외 시세 조회 및 주문 시나리오")

        default_exch = "FCME"
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch})") or default_exch
        default_symbol = self.config.get("symbols", {}).get("overseas", "6AU26")
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})")
        if not symbol:
            symbol = default_symbol

        print_info(f"[1/2] 해외 현재가 조회 중... (종목: {symbol})")
        quote_api = endpoints.OS_QUOTE_PRICE
        path = quote_api["path"]
        body = {
            "Iccurs1": {
                "iccurs1_exch_cd": exch_cd,
                "iccurs1_sym": symbol
            }
        }

        url = f"{self.client.base_url}{path}"
        headers = self.client._get_headers()
        log_request(self.logger, "POST", url, headers, body)

        quote_data, status_code, resp_headers = self.client.post(path, body=body)
        log_response(self.logger, status_code, resp_headers, quote_data)

        if status_code != 200:
            print_error(f"현재가 조회 실패 (상태: {status_code})")
            print_result("오류 응답", quote_data)
            return

        print_success("해외 현재가 조회 완료")
        print_result("해외 현재가 조회 결과", quote_data)

        proceed = get_user_input("주문을 진행하시겠습니까? (y/n)")
        if proceed.lower() != 'y':
            print_info("주문을 취소하고 메뉴로 돌아갑니다.")
            return

        print_menu("호가 구분 코드를 선택하세요", ["주문신규 (1)", "정정 (2)", "취소 (3)"])
        qt_div = get_user_input("선택")
        qt_div_cd = qt_div if qt_div in ["1", "2", "3"] else "1"

        print_menu("매수/매도를 선택하세요", ["매수 (1)", "매도 (2)"])
        sll_buy = get_user_input("선택")
        trd_div_cd = "1" if sll_buy == "1" else "2"

        print_menu("주문 유형을 선택하세요", ["시장가 (1)", "지정가 (2)", "STOP-M (3)", "STOP-L (4)"])
        nmpr = get_user_input("선택")
        glb_ord_tp_cd = nmpr if nmpr in ["1", "2", "3", "4"] else "1"

        # 주문수량 (ord_qty): 신규(1), 정정(2)일 때 필수
        if qt_div_cd in ["1", "2"]:
            while True:
                ord_qty = get_user_input("주문 수량을 입력하세요").strip()
                if ord_qty and ord_qty != "0":
                    break
                print_error("신규 및 정정 주문은 주문 수량이 필수입니다.")
        else:
            ord_qty = "0"  # 취소 주문인 경우

        #  해외주문유형이 지정가(2), STOP-L(4)일 때 입력
        if glb_ord_tp_cd in ["2", "4"]:
            while True:
                ord_pric = get_user_input("주문 가격을 입력하세요").strip()
                if ord_pric:
                    break
                print_error("지정가, STOP-L 주문은 주문 가격을 입력해야 합니다.")
        else:
            ord_pric = "0"

        #  해외주문유형이 STOP-M(3), STOP-L(4)일 때 입력
        if glb_ord_tp_cd in ["3", "4"]:
            while True:
                stop_pric = get_user_input("스탑가격을 입력하세요").strip()
                if stop_pric:
                    break
                print_error("STOP-M, STOP-L 주문은 스탑가격을 입력해야 합니다.")
        else:
            stop_pric = ""

        # 원주문번호: 정정(2), 취소(3)일 때 필수
        if qt_div_cd in ["2", "3"]:
            while True:
                org_ord_no = get_user_input("원주문번호를 입력하세요").strip()
                if org_ord_no:
                    org_ord_no = org_ord_no.zfill(10)
                    break
                print_error("정정 및 취소 주문은 원주문번호를 입력해야 합니다.")
        else:
            org_ord_no = "0".zfill(10) # 기본값 0

        order_body = {
            "qt_div_cd": qt_div_cd,
            "sym": symbol,
            "trd_div_cd": trd_div_cd,
            "glb_ord_tp_cd": glb_ord_tp_cd,
            "ord_qty": ord_qty,
            "ord_pric": ord_pric,
            "stop_pric": stop_pric,
            "org_ord_no": org_ord_no
        }

        print_info("[2/2] 해외 주문 실행 중...")
        order_api = endpoints.OS_TRADE_ORDER
        order_path = order_api["path"]

        url = f"{self.client.base_url}{order_path}"
        headers = self.client._get_headers()
        log_request(self.logger, "POST", url, headers, order_body)

        order_data, status_code, resp_headers = self.client.post(order_path, body=order_body)
        log_response(self.logger, status_code, resp_headers, order_data)

        if status_code == 200:
            print_success("해외 주문 실행 완료!")
            print_result("주문 결과", order_data)
        else:
            print_error(f"주문 실행 실패 (상태: {status_code})")
            print_result("오류 응답", order_data)
