"""
NH선물 REST API 해외 API 실행 모듈

전체_API_문서.xlsx 명세에 의거하여 API별 필요한 입력값만 선택적으로 수집하고
정확한 파라미터 Body를 생성하여 호출합니다.
"""

from datetime import datetime
from api import endpoints
from utils.display import (
    print_menu, print_result, print_info, print_error,
    print_success, get_user_input
)
from utils.logger import log_request, log_response


def _execute_quote_api(client, api_def: dict, config: dict, logger):
    path = api_def["path"]
    default_exch = "FCME"
    default_symbol = config.get("symbols", {}).get("overseas", "6AU26")
    today_str = datetime.now().strftime("%Y%m%d")
    body = {}

    if "bid-price" in path: # 해외_호가
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch})") or default_exch
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        body = {"exch_cd": exch_cd, "sym": symbol}
    elif "product-expiry" in path: # 해외_만기일조회
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        rem_dy = get_user_input(f"잔존일 입력 (기본값: 30)") or "30"
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        fut_opt_div_cd = get_user_input(f"상품구분 입력 (기본값: 공백)") or ""
        body = {"nxt_key": nxt_key, "rem_dy": rem_dy, "sym": sym, "fut_opt_div_cd": fut_opt_div_cd}
    elif path.endswith("/price"): # 해외_현재가
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch})") or default_exch
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        body = {
            "Iccurs1": {
                "iccurs1_exch_cd": exch_cd,
                "iccurs1_sym": symbol
            }
        }
    elif "chart-daily" in path: # 해외_차트(일)
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch})") or default_exch
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        inq_strt_dt = get_user_input(f"시작일자 입력 (YYYYMMDD, 기본값: 00000000)") or "00000000"   
        inq_ed_dt = get_user_input(f"종료일자 입력 (YYYYMMDD, 기본값: 99999999)") or "99999999"
        while True:
            val = get_user_input("요청건수 입력 (기본값: 300)") or "300"
            if int(val) <= 9999:
                req_qty = val
                break
            print("최대 9999건까지 요청 가능합니다.")
        print_menu("연결선물여부 선택 (기본값: 안함)", ["안함 (0)", "연결 (1)"], 0)
        cidx = get_user_input("선택")
        cidx_yn = "1" if cidx == "1" else "0"
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 99999999)") or "99999999"
        body = {"exch_cd": exch_cd, "sym": symbol, "inq_strt_dt": inq_strt_dt, "inq_ed_dt": inq_ed_dt, "req_qty": req_qty, "cidx_yn": cidx_yn, "nxt_key": nxt_key}
    elif "chart-minute" in path: # 해외_차트(분)
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch})") or default_exch
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        inq_strt_dt = get_user_input(f"조회시작일자 입력 (YYYYMMDD, 기본값: 00000000)") or "00000000"
        strt_tm = get_user_input(f"시작시간 입력 (HHMMSS, 기본값: 000000)") or "000000"
        inq_ed_dt = get_user_input(f"조회종료일 입력 (YYYYMMDD, 기본값: 99999999)") or "99999999"
        ed_tm = get_user_input(f"종료시간 입력 (HHMMSS, 기본값: 235959)") or "235959"
        req_qty = get_user_input(f"요청건수 입력 (기본값: 300)") or "300"
        while True:
            val = get_user_input("요청건수 입력 (기본값: 300)") or "300"
            if int(val) <= 9999:
                req_qty = val
                break
            print("최대 9999건까지 요청 가능합니다.")
        dcnt = get_user_input(f"묶음개수 입력 (기본값: 5)") or "5"
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 99999999)") or "99999999"
        body = {"exch_cd": exch_cd, "sym": symbol, "inq_strt_dt": "00000000", "strt_tm": strt_tm, "inq_ed_dt": "99999999", "ed_tm": ed_tm, "req_qty": req_qty, "dcnt": dcnt, "cidx_yn": "0", "nxt_key": nxt_key}
    elif "price-all-option" in path: # 해외_옵션전체시세
        default_exch_option = "OCME"
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch_option})") or default_exch_option
        default_symbol_option = "O_ESU26"
        symbol = get_user_input(f"월물품목코드 입력 (기본값: {default_symbol_option})") or default_symbol_option
        body = {"exch_cd": exch_cd, "sym": symbol,}
    elif "product-detail" in path: # 해외_품목별세부정보
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        fut_opt_div_cd = get_user_input(f"상품구분 입력 (기본값: 전체)") or ""
        prd_grp_cd = get_user_input(f"품목그룹 입력 (기본값: 전체)") or ""
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: 전체)") or ""
        cur_cd = get_user_input(f"통화코드 입력 (기본값: 전체)") or ""
        print_menu("결제구분 선택 (기본값: 전체)", ["현금결제 (1)", "실물인수도 (2)"])
        sett = get_user_input("선택")
        sett_cd = sett if sett in ["1", "2"] else ""
        print_menu("검색구분 선택 (기본값: 전체)", ["품목코드 (1)", "품목명 (2)"])
        prd = get_user_input("선택")
        prd_cd = prd if prd in ["1", "2"] else ""
        # 검색구분이 1일 때 품목명 처리
        prd_nm = ""
        if prd_cd in ["1"]:
            print_menu("품목명 선택 (기본값: 검색어 없음)", [
                "품목명 입력 (1)",
                "공백 (2)"
            ])
            nm_choice = get_user_input("선택")

            if nm_choice == "1":
                while True:
                    prd_nm = get_user_input("품목명 입력").strip()
                    if prd_nm:
                        break
                    print_error("1을 선택한 경우 품목명이 필수입니다.")

            else:
                prd_nm = "" 
        body = {"nxt_key": nxt_key, "fut_opt_div_cd": fut_opt_div_cd, "prd_grp_cd": prd_grp_cd, "exch_cd": exch_cd, "cur_cd": cur_cd, "sett_cd": sett_cd, "prd_cd": prd_cd, "prd_nm": prd_nm}
    elif "market-operations" in path: # 해외_장운영정보
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        fut_opt_div_cd = get_user_input(f"상품구분 입력 (기본값: 전체)") or ""
        prd_grp_cd = get_user_input(f"품목그룹 입력 (기본값: 전체)") or ""
        exch_cd = get_user_input(f"거래소코드 입력 (기본값: {default_exch})") or default_exch
        curr_cd = get_user_input(f"통화코드 입력 (기본값: KRW)") or "KRW"
        print_menu("검색구분 선택 (기본값: 전체)", ["품목코드 (1)", "품목명 (2)"])
        prd = get_user_input("선택")
        prd_cd = prd if prd in ["1", "2"] else ""
        # 검색구분이 1일 때 품목명 처리
        prd_nm = ""
        if prd_cd in ["1"]:
            print_menu("품목명 선택 (기본값: 검색어 없음)", [
                "품목명 입력 (1)",
                "공백 (2)"
            ])
            nm_choice = get_user_input("선택")

            if nm_choice == "1":
                while True:
                    prd_nm = get_user_input("품목명 입력").strip()
                    if prd_nm:
                        break
                    print_error("1을 선택한 경우 품목명이 필수입니다.")

            else:
                prd_nm = "" 
        body = {"nxt_key": nxt_key, "fut_opt_div_cd": fut_opt_div_cd, "prd_grp_cd": prd_grp_cd, "exch_cd": exch_cd, "cur_cd": curr_cd, "prd_cd": prd_cd, "prd_nm": prd_nm}
    else:
        body = {}

    print_info(f"{api_def['name']} 실행 중...")

    url = f"{client.base_url}{path}"
    headers = client._get_headers()
    log_request(logger, "POST", url, headers, body)

    data, status_code, resp_headers = client.post(path, body=body)

    log_response(logger, status_code, resp_headers, data)

    if status_code == 200:
        print_success(f"{api_def['name']} 완료 (상태: {status_code})")
        print_result(api_def["name"], data)
    else:
        print_error(f"{api_def['name']} 실패 (상태: {status_code})")
        print_result("오류 응답", data)


def _execute_trade_api(client, api_def: dict, config: dict, logger):
    path = api_def["path"]
    default_symbol = config.get("symbols", {}).get("overseas", "6AU26")
    today_str = datetime.now().strftime("%Y%m%d")
    body = {}

    if "order" in path and "orderable" not in path and "order-open" not in path and "order-error" not in path and "order-history" not in path:
        # 해외_주문
        print_menu("호가구분코드 선택", ["신규 (1)", "정정 (2)", "취소 (3)"])
        qt_div = get_user_input("선택")
        qt_div_cd = qt_div if qt_div in ["1", "2", "3"] else "1"

        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol

        print_menu("매수/매도 선택", ["매수 (1)", "매도 (2)"])
        sll_buy = get_user_input("선택")
        trd_div_cd = "1" if sll_buy == "1" else "2"

        print_menu("주문유형 선택", ["시장가 (1)", "지정가 (2)", "STOP-M (3)", "STOP-L (4)"])
        nmpr = get_user_input("선택")
        glb_ord_tp_cd = nmpr if nmpr in ["1", "2", "3", "4"] else "1"

        # 주문수량 (ord_qty): 신규(1), 정정(2)일 때 필수
        if qt_div_cd in ["1", "2"]:
            while True:
                ord_qty = get_user_input("주문수량 입력").strip()
                if ord_qty and ord_qty != "0":
                    break
                print_error("신규 및 정정 주문은 주문수량이 필수입니다.")
        else:
            ord_qty = "0"  # 취소 주문인 경우

        #  해외주문유형이 지정가(2), STOP-L(4)일 때 입력
        if glb_ord_tp_cd in ["2", "4"]:
            while True:
                ord_pric = get_user_input("주문가격 입력").strip()
                if ord_pric:
                    break
                print_error("지정가, STOP-L 주문은 주문가격이 필수입니다.")
        else:
            ord_pric = "0"

        #  해외주문유형이 STOP-M(3), STOP-L(4)일 때 입력
        if glb_ord_tp_cd in ["3", "4"]:
            while True:
                stop_pric = get_user_input("스탑가격 입력").strip()
                if stop_pric:
                    break
                print_error("STOP-M, STOP-L 주문은 스탑가격이 입력 항목입니다.")
        else:
            stop_pric = ""

        # 원주문번호 (org_ord_no): 정정(2), 취소(3)일 때 필수
        if qt_div_cd in ["2", "3"]:
            while True:
                org_ord_no = get_user_input("원주문번호 입력").strip()
                if org_ord_no:
                    org_ord_no = org_ord_no.zfill(10)
                    break
                print_error("정정 및 취소 주문은 원주문번호가 필수입니다.")
        else:
            org_ord_no = "0".zfill(10)  # 샘플값 0

        body = {
            "qt_div_cd": qt_div_cd,
            "sym": symbol,
            "trd_div_cd": trd_div_cd,
            "glb_ord_tp_cd": glb_ord_tp_cd,
            "ord_qty": ord_qty,
            "ord_pric": ord_pric,
            "stop_pric": stop_pric,
            "org_ord_no": org_ord_no
        }
    elif "orderable-quantity" in path: # 해외_주문가능수량
        symbol = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        print_menu("주문유형 선택", ["시장가 (1)", "지정가 (2)", "STOP-M (3)", "STOP-L (4)"])
        nmpr = get_user_input("선택")
        glb_ord_tp_cd = nmpr if nmpr in ["1", "2", "3", "4"] else "1"

        #  해외주문유형이 STOP 주문의 유형일 때 필수
        if glb_ord_tp_cd in ["3", "4"]:
            while True:
                stop_pric = get_user_input("스탑가격 입력").strip()
                if stop_pric:
                    break
                print_error("STOP-M, STOP-L 주문은 스탑가격이 필수입니다.")
        else:
            stop_pric = "0"

        ord_pric = get_user_input(f"주문가격 입력 (기본값: 0)") or "0"
        body = {
            "sym": symbol,
            "glb_ord_tp_cd": glb_ord_tp_cd,
            "ord_pric": ord_pric,
            "stop_pric": stop_pric,
        }
    elif "open-interest" in path: # 해외_잔고내역
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        body = {"nxt_key": nxt_key}
    elif "order-error" in path: #  해외_주문오류내역
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        inq_dt = get_user_input(f"조회일자 입력 (YYYYMMDD, 기본값: {today_str})") or today_str
        body = {"nxt_key": nxt_key, "inq_dt": inq_dt}
    elif "order-history" in path: # 해외_주문내역
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        print_menu("조회구분 선택", ["전체 (0)", "주문 (1)", "체결 (2)", "미체결 (3)", "미체결 지정청산(4)"], 0)
        inq = get_user_input("선택")
        inq_div = inq if inq in ("1", "2", "3", "4") else "0"
        prd_cd = get_user_input(f"품목코드 입력 (기본값: 공백)") or ""
        print_menu("매수/매도 선택", ["전체 (0)", "매수 (1)", "매도 (2)"], 0)
        sll_buy = get_user_input("선택")
        trd_div_cd = sll_buy if sll_buy in ("1", "2") else "0"

        body = {"nxt_key": nxt_key  , "inq_div": inq_div, "prd_cd": prd_cd, "trd_div_cd": trd_div_cd}
    elif "deposit" in path: # 해외_예수금조회
        biz_dt = get_user_input(f"영업일자 입력 (YYYYMMDD, 기본값: {today_str})") or today_str
        cur_cd = get_user_input(f"통화코드 입력 (기본값: USD)") or "USD"
        print_menu("환산구분 선택", ["개별 (1)", "환산 (2)"])
        cvs_cd = get_user_input("선택")
        cvs_div = "1" if cvs_cd == "1" else "2"
        body = {"biz_dt": biz_dt, "cur_cd": cur_cd, "cvs_div": cvs_div}
    elif "cumulative-pl" in path: # 해외_누적손익현황
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        inq_strt_dt = get_user_input(f"조회시작일자 입력 (YYYYMMDD, 기본값: {today_str})") or today_str
        prd_cd = get_user_input(f"품목코드 입력 (기본값: 전체)") or ""
        cvs_cur_cd = get_user_input(f"환산통화코드 입력 (기본값: USD)") or "USD"
        cur_cd = get_user_input(f"통화코드 입력 (기본값: 전체)") or ""
        body = {
            "nxt_key": nxt_key,
            "inq_strt_dt": inq_strt_dt,
            "inq_ed_dt": today_str,
            "prd_cd": prd_cd,
            "cvs_cur_cd": cvs_cur_cd,
            "cur_cd": cur_cd
        }
    elif "open-interest-expiry" in path: # 해외_보유포지션만기조회
        nxt_key = get_user_input(f"다음데이터키 입력 (기본값: 공백)") or ""
        und_sym = get_user_input(f"기초자산선물품목 입력 (기본값: 전체)") or ""
        inq_dy_cnt = get_user_input(f"조회할 최대 잔존일 입력 (기본값: 2000)") or "2000"
        body = {
            "nxt_key": nxt_key,
            "und_sym": und_sym,
            "inq_dy_cnt": inq_dy_cnt
        }
    else:
        body = {}


    print_info(f"{api_def['name']} 실행 중...")

    url = f"{client.base_url}{path}"
    headers = client._get_headers()
    log_request(logger, "POST", url, headers, body)

    data, status_code, resp_headers = client.post(path, body=body)

    log_response(logger, status_code, resp_headers, data)

    if status_code == 200:
        print_success(f"{api_def['name']} 완료 (상태: {status_code})")
        print_result(api_def["name"], data)
    else:
        print_error(f"{api_def['name']} 실패 (상태: {status_code})")
        print_result("오류 응답", data)


def run_overseas_quote(client, config: dict, logger):
    apis = endpoints.OS_QUOTE_APIS
    options = [api["name"] for api in apis] + ["← 이전 메뉴"]
    print_menu("해외 시세 API를 선택하세요", options)
    choice = get_user_input("선택")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(apis):
            _execute_quote_api(client, apis[idx], config, logger)
    except (ValueError, IndexError):
        pass


def run_overseas_trade(client, config: dict, logger):
    apis = endpoints.OS_TRADE_APIS
    options = [api["name"] for api in apis] + ["← 이전 메뉴"]
    print_menu("해외 계좌 API를 선택하세요", options)
    choice = get_user_input("선택")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(apis):
            _execute_trade_api(client, apis[idx], config, logger)
    except (ValueError, IndexError):
        pass