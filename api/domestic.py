"""
NH선물 REST API 국내(주간/야간) API 실행 모듈

전체_API_문서.xlsx 명세에 의거하여 API별 필요한 입력값(종목코드, 영업일자, 시장ID 등)만
선택적으로 프롬프트를 띄우고 정확한 파라미터 Body를 생성하여 호출합니다.
"""

from datetime import datetime

from rich.table import Table
from api import endpoints
from utils.display import (
    print_menu, print_result, print_info, print_error,
    print_success, get_user_input
)
from utils.logger import log_request, log_response

from rich.console import Console
console = Console()

def _execute_quote_api(client, api_def: dict, config: dict, logger):
    """
    국내 시세 API 공통 실행 함수
    """
    path = api_def["path"]
    default_symbol = config.get("symbols", {}).get("domestic", "A0169000")
    today_str_yyyymmdd = datetime.now().strftime("%Y%m%d")
    today_str_yymmdd = datetime.now().strftime("%y%m%d")
    body = {}

    # === API별 개별 입력 파라미터 검증 및 수집 ===
    if "price-night" in path or "price-expect-fill" in path or path.endswith("/price"): # 현재가, 현재가(야간)
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        body = {"sym": sym}
    elif "price-all-option-night" in path: # 옵션전체시세(야간)
        prd = get_user_input(
            "품목코드 입력\n"
            "  01: 코스피200\n"
            "  05: 미니코스피200\n"
            "  06: 코스닥150\n"
            "  09: 코스피200위클리(목)\n"
            "  AF: 코스피200위클리(목)\n"
            "  AJ: 코스닥150위클리(목)\n"
            "  AK: 코스닥150위클리(월)\n"
            "(기본값: 01)"
        ) or "01"
        exp_mon = get_user_input(f"만기년월 입력 (YYMMDD, 기본값: {today_str_yymmdd})") or today_str_yymmdd
        nxt_stkr_pric = get_user_input("다음 행사가 입력 (기본값: 99999999)") or "99999999"
        body = {"prd": prd, "exp_mon": exp_mon, "nxt_stkr_pric": nxt_stkr_pric}
    elif "price-bid" in path: # 호가
        exch_cd = get_user_input("거래소코드 입력 (기본값: KSP)") or "KSP"
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        body = {"exch_cd": exch_cd, "sym": sym}
    elif "chart-daily" in path: # 차트(일)
        print_menu("주간/야간 구분 선택", ["주간 (1)", "야간 (2)"])
        nght = get_user_input("선택")
        nght_tp = nght if nght in ("1", "2") else "1"
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        inq_strt_dt = get_user_input(f"조회 시작일 입력 (YYYYMMDD, 기본값: 00000000)") or "00000000"
        inq_ed_dt = get_user_input(f"조회 종료일 입력 (YYYYMMDD, 기본값: 99999999)") or "99999999"
        while True:
            val = get_user_input("요청건수 입력 (기본값: 300)") or "300"
            if int(val) <= 9999:
                req_qty = val
                break
            print("최대 9999건까지 요청 가능합니다.")
        print_menu("연결지수여부 선택", ["안함 (0)", "연결 (1)"], 0)
        cidx = get_user_input("선택")
        cidx_yn = cidx if cidx in ("0", "1") else "0"
        nxt_key = get_user_input("다음데이터키 입력 (기본값: 99999999)") or "99999999"
        print_menu("연속선물 만기수정 선택", ["수정안함 (0)", "만기수정 (1)"], 0)
        fut_cidx_exp = get_user_input("선택")
        fut_cidx_exp_mod = fut_cidx_exp if fut_cidx_exp in ("0", "1") else "0"
        body = {"nght_tp": nght_tp, "sym": sym, "inq_strt_dt": inq_strt_dt, "inq_ed_dt": inq_ed_dt, "req_qty": req_qty, "cidx_yn": cidx_yn, "nxt_key": nxt_key, "fut_cidx_exp_mod": fut_cidx_exp_mod}
    elif "chart-minute" in path: # 차트(분)
        print_menu("주간/야간 구분 선택", ["주간 (1)", "야간 (2)"])
        nght = get_user_input("선택")
        nght_tp = nght if nght in ("1", "2") else "1"
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        inq_strt_dt = get_user_input(f"조회시작일자 입력 (YYYYMMDD, 기본값: 00000000)") or "00000000"
        strt_tm = get_user_input(f"시작시간 입력 (HHMMSS, 기본값: 000000)") or "000000"
        inq_ed_dt = get_user_input(f"조회종료일자 입력 (YYYYMMDD, 기본값: 99999999)") or "99999999"
        ed_tm = get_user_input(f"종료시간 입력 (HHMMSS, 기본값: 235959)") or "235959"
        while True:
            val = get_user_input("요청개수 입력 (기본값: 300)") or "300"
            if int(val) <= 9999:
                req_qty = val
                break
            print("최대 9999건까지 요청 가능합니다.")
        dcnt = get_user_input(f"묶음개수 입력 (기본값: 5)") or "5"
        print_menu("연결지수여부 선택", ["안함 (0)", "연결 (1)"], 0)
        cidx = get_user_input("선택")
        cidx_yn = cidx if cidx in ("0", "1") else "0"
        nxt_key = get_user_input("다음데이터키 입력 (기본값: 99999999)") or "99999999"
        print_menu("연속선물 만기수정 선택", ["수정안함 (0)", "만기수정 (1)"], 0)
        fut_cidx_exp = get_user_input("선택")
        fut_cidx_exp_mod = fut_cidx_exp if fut_cidx_exp in ("0", "1") else "0"
        body = {"nght_tp": nght_tp, "sym": sym, "inq_strt_dt": inq_strt_dt, "strt_tm": strt_tm, "inq_ed_dt": inq_ed_dt, "ed_tm": ed_tm, "req_qty": req_qty, "dcnt": dcnt, "cidx_yn": cidx_yn, "nxt_key": nxt_key, "fut_cidx_exp_mod": fut_cidx_exp_mod}
    elif "price-all-futures" in path: # 선물전체시세
        console.print("  품목코드")
        console.print()

        table = Table.grid(padding=(0, 4))
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_column()

        table.add_row("01: KOSPI",  "05: MKOSPI", "06: KOSDAQ", "AG: KOSDAQGLOBAL")
        table.add_row("08: KRX300", "04: VKOSPI",  "75: USD",    "77: EUR")
        table.add_row("76: JPY",    "78: CNH",     "65: KTB",    "67: 10KTB")
        table.add_row("66: 5KTB",   "70: 30KTB",   "",           "")

        console.print(table)
        console.print()

        sector_table = Table.grid(padding=(0, 6))
        sector_table.add_column()
        sector_table.add_column()

        sector_table.add_row("A3: K200경기소비재", "A2: K200금융")
        sector_table.add_row("A0: K200에너지",     "A1: K200정보기술")
        sector_table.add_row("AC: BBIG",           "AD: 2차전지TOP10")
        sector_table.add_row("AE: 바이오TOP10",    "AL: KRX반도체지수")

        console.print(sector_table)
        console.print()

        prd = get_user_input("품목코드 입력 (기본값: 01)") or "01"
    
        body = {"prd": prd}
    elif "price-all-option" in path: # 옵션전체시세
        prd = get_user_input("품목코드 입력 (기본값: 01)") or "01"
        exp_mon = get_user_input(f"만기년월 입력 (YYMMDD, 기본값: {today_str_yymmdd})") or today_str_yymmdd
        nxt_stkr_pric = get_user_input("다음 행사가 입력 (기본값: 99999999)") or "99999999"
        body = {"prd": prd, "exp_mon": exp_mon, "nxt_stkr_pric": nxt_stkr_pric}
    elif "trend-investor" in path: # 투자자직전매매동향
        opt_prd = get_user_input("품목선물옵션코드 입력 (기본값: 011)") or "011"
        ref_dt = get_user_input(f"기준일 입력 (YYYYMMDD, 기본값: {today_str_yyyymmdd})") or today_str_yyyymmdd
        print_menu("투자자조회구분 선택", ["수량 (1)", "금액 (2)"])
        inq = get_user_input("선택")
        inq_tp = inq if inq in ("1", "2") else "1"
        body = {"opt_prd": opt_prd, "ref_dt": ref_dt, "inq_tp": inq_tp}
    elif "price-expect-fill" in path: # 종목예상체결가
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol
        body = {"sym": sym}
    elif "product-detail" in path: # 품목별 세부정보: 파라미터 없음
        body = {}
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
    """
    국내 계좌 API 공통 실행 함수
    """
    path = api_def["path"]
    default_symbol = config.get("symbols", {}).get("domestic", "A0169000")
    today_str = datetime.now().strftime("%Y%m%d")
    body = {}

    if "order" in path and "order-open" not in path and "orderable" not in path and "order-error" not in path and "order-history" not in path: # 신규주문, 신규주문(야간)
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol

        print_menu("매수/매도 선택", ["매수 (1)", "매도 (2)"])
        sll_buy = get_user_input("선택")
        trd_div = "1" if sll_buy == "1" else "2" 

        print_menu("주문유형 선택", ["지정가 (1)", "시장가 (2)", "조건부 (3)", "최유리 (4)"])
        nmpr = get_user_input("선택")
        ord_tp_cd = nmpr if nmpr in ("1", "2", "3", "4") else "1"

        ord_qty = get_user_input("주문수량 (기본값: 1)") or "1"

        # 주문가격: 지정가(1), 조건부(3)일 때 입력
        if ord_tp_cd in ("1", "3"):
            while True:
                price = get_user_input("주문가격 입력").strip()
                if price and price != "0":
                    break
                print_error("지정가 및 조건부 주문은 주문가격이 필수입니다.")
        else:
            price = ""  # 시장가, 최유리인 경우

        print_menu("체결조건구분 선택", ["FAS (1)", "FOK (2)", "FAK (3)"])
        exec_cnd = get_user_input("선택")
        exec_cnd_cd = exec_cnd if exec_cnd in ("1", "2", "3") else "1"

        body = {
            "sym": sym,
            "trd_div": trd_div,
            "ord_tp_cd": ord_tp_cd,
            "ord_qty": ord_qty,
            "ord_pric": price,
            "exec_cnd_cd": exec_cnd_cd,
        }
    elif "modify" in path: # 정정주문, 정정주문(야간)
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol

        print_menu("매수/매도 선택", ["매수 (1)", "매도 (2)"])
        sll_buy = get_user_input("선택")
        trd_div = "1" if sll_buy == "1" else "2"

        print_menu("주문유형 선택", ["지정가 (1)", "시장가 (2)", "조건부 (3)", "최유리 (4)"])
        nmpr = get_user_input("선택")
        ord_tp_cd = nmpr if nmpr in ("1", "2", "3", "4") else "1"

        ord_qty = get_user_input("주문수량 (기본값: 1)") or "1"
        ord_pric = get_user_input("주문가격 입력 (기본값: 0)") or "0"

        print_menu("체결조건구분 선택", ["FAS (1)", "FOK (2)", "FAK (3)"])
        exec_cnd = get_user_input("선택")
        exec_cnd_cd = exec_cnd if exec_cnd in ("1", "2", "3") else "1"

        while True:
            org_ord_no = get_user_input("원주문번호 입력").strip()
            if org_ord_no:
                break
            print_error("원주문번호는 필수입니다.")

        org_ord_no = org_ord_no.zfill(10)

        body = {
            "sym": sym,
            "trd_div": trd_div,
            "ord_tp_cd": ord_tp_cd,
            "ord_qty": ord_qty,
            "ord_pric": ord_pric,
            "exec_cnd_cd": exec_cnd_cd,
            "org_ord_no": org_ord_no,
        }
    elif "cancel" in path: # 취소주문, 취소주문(야간)
        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol

        print_menu("매수/매도 선택", ["매수 (1)", "매도 (2)"])
        sll_buy = get_user_input("선택")
        trd_div = "1" if sll_buy == "1" else "2"

        ord_qty = get_user_input("주문수량 입력 (기본값: 0)") or "0"

        while True:
            org_ord_no = get_user_input("원주문번호 입력").strip()
            if org_ord_no:
                break
            print_error("원주문번호는 필수입니다.")
            
        org_ord_no = org_ord_no.zfill(10)

        body = {
            "sym": sym,
            "trd_div": trd_div,
            "ord_qty": ord_qty,
            "org_ord_no": org_ord_no,
        }
    elif "orderable-quantity" in path: # 주문가능수량
        print_menu("처리구분 선택", ["주간_일반 (1)", "주간_법인 (2)", "야간_일반 (3)", "야간_법인 (4)"])
        ord = get_user_input("선택")
        ord_sts = ord if ord in ( "1", "2", "3", "4") else "1"

        sym = get_user_input(f"종목코드 입력 (기본값: {default_symbol})") or default_symbol

        print_menu("매수/매도 선택", ["매수 (1)", "매도 (2)"])
        trd = get_user_input("선택")
        trd_div = "1" if trd == "1" else "2"

        ord_pric = get_user_input("주문가격 입력 (기본값: 0)") or "0"
        body = {
            "ord_sts": ord_sts,
            "sym": sym,
            "trd_div": trd_div,
            "ord_pric": ord_pric,
        }
    elif "open-interest" in path: # 잔고내역
        nxt_key = get_user_input("다음데이터키 입력 (기본값: 공백)") or ""
        body = {"nxt_key": nxt_key}
    elif "order-error" in path: # 주문오류내역 
        inq_dt = get_user_input(f"조회일자 입력 (YYYYMMDD, 기본값: {today_str})") or today_str

        print_menu("매수/매도 선택", ["전체 (0)", "매수 (1)", "매도 (2)"], 0)
        trd_div = get_user_input("선택")
        trd_div_cd = trd_div if trd_div in ("0", "1", "2") else "0"

        nxt_key = get_user_input("다음데이터키 입력 (기본값: 공백)") or ""
        body = {
            "inq_dt": inq_dt,
            "trd_div_cd": trd_div_cd,
            "nxt_key": nxt_key,
        }
    elif "order-history" in path: # 주문내역 
        print_menu("매수/매도 선택", ["전체 (0)", "매수 (1)", "매도 (2)"], 0)
        trd = get_user_input("선택")
        trd_div = trd if trd in ("0", "1", "2") else "0"

        print_menu("체결구분 선택", ["전체 (0)", "체결 (1)", "미체결 (2)", "미접수 (3)"], 0)
        exec = get_user_input("선택")
        exec_div = exec if exec in ("0", "1", "2", "3") else "0"

        print_menu("거래시간구분 선택", ["전체 (0)", "주간 (1)", "야간 (2)"], 0)
        trd_tm_div = get_user_input("선택")
        trd_tm_div_cd = trd_tm_div if trd_tm_div in ("0", "1", "2") else "0"

        print_menu("주문구분 선택", ["전체 (0)", "거부 (1)", "오류 (2)"], 0)
        ord_div = get_user_input("선택")
        ord_div_cd = ord_div if ord_div in ("0", "1", "2") else "0"

        nxt_key = get_user_input("다음데이터키 입력 (기본값: 공백)") or ""
        body = {
            "trd_div": trd_div,
            "exec_div": exec_div,
            "trd_tm_div_cd": trd_tm_div_cd,
            "ord_div_cd": ord_div_cd,
            "nxt_key": nxt_key,
        }
    elif "deposit" in path: # 예수금조회
        biz_dt = get_user_input(f"영업일자 입력 (YYYYMMDD, 기본값: {today_str})") or today_str
        body = {"biz_dt": biz_dt}

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


def run_domestic_day_quote(client, config: dict, logger):
    apis = endpoints.DM_QUOTE_APIS
    options = [api["name"] for api in apis] + ["← 이전 메뉴"]
    print_menu("국내(주간) 시세 API를 선택하세요", options)
    choice = get_user_input("선택")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(apis):
            _execute_quote_api(client, apis[idx], config, logger)
    except (ValueError, IndexError):
        pass


def run_domestic_day_trade(client, config: dict, logger):
    apis = endpoints.DM_TRADE_APIS
    options = [api["name"] for api in apis] + ["← 이전 메뉴"]
    print_menu("국내(주간) 계좌 API를 선택하세요", options)
    choice = get_user_input("선택")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(apis):
            _execute_trade_api(client, apis[idx], config, logger)
    except (ValueError, IndexError):
        pass


def run_domestic_night_quote(client, config: dict, logger):
    apis = endpoints.DMN_QUOTE_APIS
    options = [api["name"] for api in apis] + ["← 이전 메뉴"]
    print_menu("국내(야간) 시세 API를 선택하세요", options)
    choice = get_user_input("선택")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(apis):
            _execute_quote_api(client, apis[idx], config, logger)
    except (ValueError, IndexError):
        pass


def run_domestic_night_trade(client, config: dict, logger):
    apis = endpoints.DMN_TRADE_APIS
    options = [api["name"] for api in apis] + ["← 이전 메뉴"]
    print_menu("국내(야간) 계좌 API를 선택하세요", options)
    choice = get_user_input("선택")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(apis):
            _execute_trade_api(client, apis[idx], config, logger)
    except (ValueError, IndexError):
        pass
