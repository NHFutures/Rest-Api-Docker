"""
NH선물 REST API 터미널 UI 모듈

rich 라이브러리를 사용하여 터미널에 시각적으로 보기 좋은 출력을 제공합니다.
전체_API_문서.xlsx OUTPUT 규격 필드(pask1~pask5, vask1~vask5, nask1~nask5, pbid1~pbid5, vbid1~vbid5, NowPrc 등)를
완벽하게 파싱하여 HTTP 사전 조회 시 수치가 0이 아닌 실제 데이터로 전광판 호가창에 표현되도록 조율합니다.
"""

import os
import json
import sys
from datetime import datetime
from rich.console import Console, Group
from rich.panel import Panel
from rich.pretty import pprint
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.syntax import Syntax
from rich import box

# Rich 콘솔 인스턴스
console = Console()


def clear_screen():
    """터미널 화면 초기화"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    """프로그램 헤더 출력"""
    console.print()
    console.print(Panel(
        f"[bold white]{title}[/bold white]",
        border_style="bright_blue",
        box=box.DOUBLE,
        padding=(1, 2)
    ))
    console.print()

def print_menu(title: str, options: list, start_index: int = 1):
    """번호 선택 메뉴 출력

    start_index: 메뉴 번호를 어디서부터 시작할지 지정 (기본값: 1)
    """
    console.print(f"  [bold cyan]{title}[/bold cyan]")
    console.print()
    for i, option in enumerate(options, start_index):
        console.print(f"    [bold yellow]{i}.[/bold yellow] {option}", highlight=False)
    console.print()

def print_result(title: str, data):
    """API 응답 결과 JSON 출력"""
    console.print()
    console.print(f"  [bold green]━━━ {title} ━━━[/bold green]")
    console.print()
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)
    console.print()


def print_table(title: str, headers: list, rows: list):
    """테이블 형식 데이터 출력"""
    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="bright_blue",
    )
    for header in headers:
        table.add_column(header, justify="center")
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print()
    console.print(table)
    console.print()


def print_error(message: str):
    """오류 메시지 출력 (빨간색)"""
    console.print(f"  [bold red]✗ 오류:[/bold red] {message}")


def print_success(message: str):
    """성공 메시지 출력 (초록색)"""
    console.print(f"  [bold green]✓ 성공:[/bold green] {message}")


def print_info(message: str):
    """정보 메시지 출력 (시안색)"""
    console.print(f"  [bold cyan]ℹ 정보:[/bold cyan] {message}")


def print_warning(message: str):
    """경고 메시지 출력 (노란색)"""
    console.print(f"  [bold yellow]⚠ 경고:[/bold yellow] {message}")


def get_user_input(prompt: str) -> str:
    """사용자 입력 받기"""
    try:
        return console.input(f"  [bold yellow]▶ {prompt}: [/bold yellow]").strip()
    except EOFError:
        return ""


def make_ticker_group(execution_data: dict, quote_data: dict, market_type: str, symbol: str, status_msg: str = "") -> Group:
    """
    open_api_runner 및 전체_API_문서.xlsx 규격 필드 기반 호가창/체결 Renderable 생성

    HTTP 파싱 지원 필드 키:
        - 매도호가/수량/건수: pask1~pask5, askp1~askp5, vask1~vask5, askp_rsqn1~5, nask1~nask5
        - 매수호가/수량/건수: pbid1~pbid5, bidp1~bidp5, vbid1~vbid5, bidp_rsqn1~5, nbid1~nbid5
        - 현재가/체결: NowPrc, last, clast, stck_prpr, price, Diff, diff, Rate, rate, Volume, tvol
    """
    # ── 상단 헤더
    header = Text()
    header.append(f"📊 {market_type} 전광판 | 종목코드: ", style="bold white")
    header.append(f"{symbol}", style="bold yellow")
    if status_msg:
        header.append(f" | {status_msg}", style="dim cyan")

    # ── 호가 데이터 파싱 (5단계 호가 추출)
    asks = []  # 매도호가 [{"price": "0", "qty": "0", "cnt": "0"}]
    bids = []  # 매수호가 [{"price": "0", "qty": "0", "cnt": "0"}]

    # ── 응답 키 형식 매칭
    def _lookup(d: dict, bases, idx=None, default="0"):
        if isinstance(bases, str):
            bases = [bases]
        for b in bases:
            if idx is None:
                if b in d and d[b] not in (None, ""):
                    return d[b]
            else:
                # 패턴: base{idx}, base_{idx}
                k1 = f"{b}{idx}"
                k2 = f"{b}_{idx}"
                if k1 in d and d[k1] not in (None, ""):
                    return d[k1]
                if k2 in d and d[k2] not in (None, ""):
                    return d[k2]
        for b in bases:
            if b in d and d[b] not in (None, ""):
                return d[b]
        return default

    # 엑셀 및 Postman 명세 키값 전체 탐색
    for i in range(5, 0, -1):
        ap = _lookup(quote_data, ["pask", "askp", "ask_pric", "ask_prc", "sell_price"], i, "0")
        aq = _lookup(quote_data, ["vask", "askp_rsqn", "ask_qty", "sell_qty"], i, "0")
        ac = _lookup(quote_data, ["nask", "askp_cnt", "ask_cnt"], i, "0")
        asks.append({"price": str(ap or "0"), "qty": str(aq or "0"), "cnt": str(ac or "0")})

    for i in range(1, 6):
        bp = _lookup(quote_data, ["pbid", "bidp", "bid_pric", "bid_prc", "buy_price"], i, "0")
        bq = _lookup(quote_data, ["vbid", "bidp_rsqn", "bid_qty", "buy_qty"], i, "0")
        bc = _lookup(quote_data, ["nbid", "bidp_cnt", "bid_cnt"], i, "0")
        bids.append({"price": str(bp or "0"), "qty": str(bq or "0"), "cnt": str(bc or "0")})

    # 호가 테이블 생성
    table = Table(box=box.HORIZONTALS, show_header=True, header_style="bold cyan", pad_edge=False)
    table.add_column("매도건수", justify="center", width=10, style="dim cyan")
    table.add_column("매도잔량", justify="right", style="cyan", width=14)
    table.add_column("호가 (Price)", justify="center", width=18)
    table.add_column("매수잔량", justify="left", style="bright_red", width=14)
    table.add_column("매수건수", justify="center", width=10, style="dim magenta")

    # 매도 5호가 행 (상단 파란색)
    for ask in asks:
        price_val = ask["price"]
        price_text = Text(f"{price_val}", style="bold bright_blue")
        table.add_row(
            ask["cnt"] if ask["cnt"] not in ("0", "") else "-",
            ask["qty"] if ask["qty"] not in ("0", "") else "-",
            price_text,
            "",
            "",
        )

    # 매수 5호가 행 (하단 빨간색)
    for bid in bids:
        price_val = bid["price"]
        price_text = Text(f"{price_val}", style="bold red")
        table.add_row(
            "",
            "",
            price_text,
            bid["qty"] if bid["qty"] not in ("0", "") else "-",
            bid["cnt"] if bid["cnt"] not in ("0", "") else "-",
        )

    # 총 잔량 계산 (엑셀 명세 vask, vbid 지원)
    def _to_int(val):
        try:
            if isinstance(val, int):
                return val
            s = str(val).replace(",", "")
            return int(s) if s.isdigit() else 0
        except Exception:
            return 0

    tot_vask_raw = quote_data.get("vask") or quote_data.get("vask_qty")
    tot_vbid_raw = quote_data.get("vbid") or quote_data.get("vbid_qty")
    tot_vask = _to_int(tot_vask_raw) or sum(_to_int(a["qty"]) for a in asks)
    tot_vbid = _to_int(tot_vbid_raw) or sum(_to_int(b["qty"]) for b in bids)

    table.add_row(
        "",
        Text(f"{tot_vask:,}" if isinstance(tot_vask, int) and tot_vask > 0 else str(tot_vask or "-"), style="bold cyan"),
        Text("Total 잔고", style="bold white"),
        Text(f"{tot_vbid:,}" if isinstance(tot_vbid, int) and tot_vbid > 0 else str(tot_vbid or "-"), style="bold red"),
        "",
    )

    # ── 체결 정보 테이블 (엑셀 키 탐색)
    trade_table = Table(box=box.SIMPLE_HEAD, show_header=True, pad_edge=False)
    trade_table.add_column("현재가", justify="center", width=15)
    trade_table.add_column("전일대비", justify="center", width=15)
    trade_table.add_column("등락율", justify="center", width=15)
    trade_table.add_column("체결량", justify="center", width=15)
    trade_table.add_column("누적거래량", justify="center", width=18)

    # 체결 데이터 파싱
    last_price = str(execution_data.get("last_pric") or "-")
    change_val = str(execution_data.get("diff_rt") or "-")
    change_rate = str(execution_data.get("rt") or "-")
    volume = str(execution_data.get("exec_qty") or "-")
    acc_volume = str(execution_data.get("cum_trd_qty") or "-")

    # 등락 색상 (상승 빨강, 하락 파랑)
    color = "bold red" if "-" not in change_val and change_val not in ("0", "-") else ("bold bright_blue" if "-" in change_val else "white")

    trade_table.add_row(
        Text(last_price, style=color),
        Text(change_val, style=color),
        Text(f"{change_rate}%" if change_rate != "-" and "%" not in change_rate else change_rate, style=color),
        Text(volume, style="white"),
        Text(acc_volume, style="yellow")
    )

    footer = Text("  [Ctrl+C 입력 시 이전 메뉴로 복귀합니다]", style="dim gray")

    return Group(
        Align.center(header),
        Align.center(table),
        Align.center(trade_table),
        Align.center(footer)
    )


def print_ticker_board(execution_data: dict, quote_data: dict, market_type: str):
    """단발성 전광판 렌더링"""
    group = make_ticker_group(execution_data, quote_data, market_type, "호가창")
    console.print(group)
