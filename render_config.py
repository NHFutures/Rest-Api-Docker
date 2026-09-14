#!/usr/bin/env python3
"""
컨테이너 시작 시 `config.yaml.template`을 읽어 환경변수를 반영한 `config.yaml`을 생성하고
그 다음에 실제 애플리케이션 커맨드를 실행합니다.
"""

import os
import sys
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE_DIR, "config.yaml.template")
OUT = os.path.join(BASE_DIR, "config.yaml")
DEFAULT_SYMBOLS = {
    "domestic": "A0169000",
    "overseas": "6AU26",
}


def _get_env_prefixed(primary_name, fallback_name=None):
    """환경변수의 '존재 여부'를 기준으로 우선값을 결정

    - primary_name이 os.environ에 있으면 그 값을 반환(값이 빈 문자열이어도 그대로 반환).
    - 그렇지 않으면 fallback_name으로 폴백해 os.getenv(fallback_name)를 반환.
    - 둘 다 없으면 None 반환.
    """
    if primary_name in os.environ:
        return os.environ[primary_name]
    if fallback_name:
        return os.getenv(fallback_name)
    return None


def _normalize_symbols(cfg: dict) -> bool:
    """설정 파일에 비어 있거나 placeholder인 symbol 값만 기본값으로 보완"""
    if not isinstance(cfg, dict):
        return False

    symbols = cfg.setdefault("symbols", {})
    if not isinstance(symbols, dict):
        symbols = {}
        cfg["symbols"] = symbols

    changed = False
    for symbol_key, default_value in DEFAULT_SYMBOLS.items():
        current = symbols.get(symbol_key, "")
        if current is None or str(current).strip() == "" or str(current).startswith("YOUR_"):
            symbols[symbol_key] = default_value
            changed = True
    return changed


def ensure_config_exists(template_path: str = TEMPLATE, output_path: str = OUT) -> str:
    """템플릿을 기반으로 config.yaml을 생성하고, symbol placeholder만 실제 기본값으로 채움"""
    cfg = {}

    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    if not isinstance(cfg, dict):
        cfg = {}

    changed = _normalize_symbols(cfg)
    if not os.path.exists(output_path) or changed:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, default_flow_style=False, allow_unicode=True)

    return output_path


def main():
    ensure_config_exists()

    cfg = {}
    if os.path.exists(OUT):
        with open(OUT, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    elif os.path.exists(TEMPLATE):
        with open(TEMPLATE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    # 키/시크릿
    key = _get_env_prefixed("APP_KEY")
    secret = _get_env_prefixed("APP_SECRET")

    # 환경/계정타입
    account_type = _get_env_prefixed("ACCOUNT_TYPE") or "domestic"
    env_sel = _get_env_prefixed("ENVIRONMENT")

    # 템플릿에 반영
    if isinstance(cfg, dict):
        if env_sel is not None:
            cfg["environment"] = env_sel

        symbols = cfg.setdefault("symbols", {})
        if not isinstance(symbols, dict):
            symbols = {}
            cfg["symbols"] = symbols
        for symbol_key, default_value in DEFAULT_SYMBOLS.items():
            current = symbols.get(symbol_key, "")
            if current is None or str(current).strip() == "" or str(current).startswith("YOUR_"):
                symbols[symbol_key] = default_value

        accounts = cfg.setdefault("accounts", {})
        acct = accounts.setdefault(account_type, {})

        # None이 아닌 경우에만 필드에 설정
        # 빈 문자열인 경우에는 덮어쓰지 않음 (앱 키/앱 시크릿은 실제 값이 있어야 함)
        if key is not None and str(key).strip() != "":
            acct["appkey"] = key
        if secret is not None and str(secret).strip() != "":
            acct["appsecret"] = secret

    # 결과를 파일로 기록
    with open(OUT, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, default_flow_style=False, allow_unicode=True)

    # Dockerfile의 CMD가 이 스크립트의 인수로 넘어옴.
    # 인수가 있으면 그 명령을 exec로 치환하여 실행.
    if len(sys.argv) > 1:
        os.execvp(sys.argv[1], sys.argv[1:])
    else:
        os.execvp("python", ["python", "-u", "main.py"])


if __name__ == "__main__":
    main()
