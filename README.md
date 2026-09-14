# NH Open API Docker Project

NH선물 Open API를 Python으로 연동하고, 로컬/도커 환경에서 손쉽게 테스트할 수 있도록 구성한 프로젝트입니다.

이 프로젝트는 NH선물 REST API와 WebSocket 실시간 API를 활용하여 다음 기능을 제공합니다.

- 국내선물(주간/야간) 시세 조회
- 해외선물 시세 조회
- 계좌 관련 API 호출
- 인증 토큰 발급 및 폐기
- 실시간 WebSocket 구독
- 시나리오 기반 시세 조회 → 주문 실행 흐름
- Docker 환경에서 환경변수 기반 실행 지원

---

## 1. 프로젝트 개요

본 프로젝트는 터미널 기반 인터랙티브 메뉴를 통해 NH선물 API를 직접 실행할 수 있는 구조로 설계되어 있습니다.

주요 실행 파일:

- `main.py` : 애플리케이션 메인 진입점
- `render_config.py` : `config.yaml.template`을 기반으로 `config.yaml` 생성 및 환경변수 반영
- `config.yaml.template` : 설정 템플릿
- `docker-compose.yml` : Docker Compose 실행 설정
- `Dockerfile` : 컨테이너 빌드 설정

실행 흐름은 다음과 같습니다.

1. `main.py` 실행
2. `config.yaml` 로드
3. `APP_KEY`, `APP_SECRET`, `ENVIRONMENT`, `ACCOUNT_TYPE` 환경변수 반영
4. 사용자에게 환경/계좌 선택 메뉴 제공
5. REST API 또는 WebSocket API 실행

---

## 2. 기능 구성

### 2.1 REST API

`api/` 패키지에는 NH선물 API를 카테고리별로 분리해 놓았습니다.

- `api/domestic.py` : 국내선물 API 실행 함수
- `api/overseas.py` : 해외선물 API 실행 함수
- `api/auth_api.py` : 인증 관련 메뉴 처리
- `api/endpoints.py` : API 엔드포인트 정의 및 TR 코드 관리

### 2.2 실시간 WebSocket

실시간 데이터 수신은 `nhfs_sdk/ws_client.py`와 `main.py`의 실시간 메뉴를 통해 수행됩니다.

지원 채널 예시:

- `O1` : 계좌 체결
- `FA` : 해외 체결 내역
- `FB` : 해외 호가 내역
- `KA` : 국내 주간 체결
- `KB` : 국내 주간 호가
- `KC` : 국내 야간 체결
- `KD` : 국내 야간 호가

### 2.3 시나리오 실행

`scenarios/` 디렉터리에는 실제 거래 흐름을 흉내 내는 시나리오가 포함되어 있습니다.

- `scenarios/domestic_scenario.py` : 국내 주간/야간 시세 조회 및 주문 시나리오
- `scenarios/overseas_scenario.py` : 해외 시세 조회 및 주문 시나리오
- `scenarios/realtime_scenario.py` : 실시간 데이터 결합 시나리오

### 2.4 SDK 및 공통 유틸

- `nhfs_sdk/auth.py` : access token 발급, revoke, websocket access key 발급
- `nhfs_sdk/rest_client.py` : 요청 헤더, rate limit, HTTP 통신 처리
- `utils/display.py` : 터미널 UI 출력
- `utils/logger.py` : 로그 설정 및 요청/응답 기록

---

## 3. 프로젝트 구조

```text
NH-DOCKER-API/
├─ api/
│  ├─ __init__.py
│  ├─ auth_api.py
│  ├─ domestic.py
│  ├─ endpoints.py
│  └─ overseas.py
├─ nhfs_sdk/
│  ├─ __init__.py
│  ├─ auth.py
│  ├─ rest_client.py
│  └─ ws_client.py
├─ scenarios/
│  ├─ __init__.py
│  ├─ domestic_scenario.py
│  ├─ overseas_scenario.py
│  └─ realtime_scenario.py
├─ utils/
│  ├─ __init__.py
│  ├─ display.py
│  └─ logger.py
├─ Dockerfile
├─ README.md
├─ config.yaml.template
├─ config.yaml
├─ docker-compose.yml
├─ main.py
├─ render_config.py
├─ requirements.txt
├─ logs/
└─ nh-docker-env/
```

---

## 4. 사전 준비

### 4.1 Python 환경

필수 패키지:

```bash
pip install -r requirements.txt
```

의존성:

- `requests`
- `websockets`
- `pyyaml`
- `rich`
- `truststore`

### 4.2 NH선물 APP KEY / APP SECRET

실제 API 호출을 위해서는 NH선물에서 발급받은 APP KEY와 APP SECRET이 필요합니다.

이 값은 `config.yaml` 또는 환경변수로 설정할 수 있습니다.

---

## 5. 설정 방법

### 5.1 기본 설정 파일 생성

프로젝트 루트에 `config.yaml`이 없으면 `render_config.py` 또는 초기 실행 시 자동으로 생성됩니다.

템플릿 파일 구조는 다음과 같습니다.

```yaml
environment: demo

urls:
  demo: https://apidemo.futures.co.kr
  real: https://api.futures.co.kr

accounts:
  domestic:
    appkey: "YOUR_DOMESTIC_APPKEY"
    appsecret: "YOUR_DOMESTIC_APPSECRET"
    account_no: "000000-00-0000"
    cano: "000000-00"
    acnt_prdt_cd: "0001"
  overseas:
    appkey: "YOUR_OVERSEAS_APPKEY"
    appsecret: "YOUR_OVERSEAS_APPSECRET"
    account_no: "000000-00-0000"
    cano: "000000-00"
    acnt_prdt_cd: "0001"

symbols:
  domestic: "A0169000"
  overseas: "6AU26"
```

### 5.2 환경변수 방식

Docker 혹은 비대화형 실행 환경에서는 환경변수를 통해 값 주입이 가능합니다.

```bash
export APP_KEY="your_app_key"
export APP_SECRET="your_app_secret"
export ENVIRONMENT="demo"      # demo or real
export ACCOUNT_TYPE="domestic" # domestic or overseas
```

`APP_KEY` / `APP_SECRET`은 계좌별 값으로 적용되며, `main.py`에서 환경변수 값이 우선 적용됩니다.

---

## 6. 로컬 실행

프로젝트 루트에서 다음 명령으로 실행할 수 있습니다.

```bash
python main.py
```

실행하면 다음과 같은 메뉴를 만나게 됩니다.

- 실행 환경 선택
  - 모의투자
  - 실투자
- 계좌 선택
  - 국내
  - 해외
- HTTP API 실행
- 실시간 API 실행
- 시나리오 HTTP 실행
- 인증 토큰 관리

---

## 7. Docker 실행

### 7.1 이미지 빌드

```bash
docker build -t nh-open-api .
```

### 7.2 컨테이너 실행

```bash
docker run -it \
  --env APP_KEY=your_app_key \
  --env APP_SECRET=your_app_secret \
  --env ENVIRONMENT=demo \
  --env ACCOUNT_TYPE=domestic \
  nh-open-api
```

### 7.3 Docker Compose 실행

```bash
docker-compose up --build
```

`docker-compose.yml`에서는 다음 환경변수를 설정할 수 있습니다.

```yaml
environment:
  - APP_KEY=${APP_KEY:-}
  - APP_SECRET=${APP_SECRET:-}
  - ENVIRONMENT=${ENVIRONMENT:-}
  - ACCOUNT_TYPE=${ACCOUNT_TYPE:-}
```

실제 운영 환경에서는 `.env` 파일 또는 호스트 환경변수로 값을 주입하는 방식을 권장합니다.

---

## 8. 사용 예시

### 8.1 인증 토큰 발급

실행 메뉴에서 인증 옵션을 선택하면 `auth-service/v1/token`에 접근해 access token을 발급받습니다.

- `get_access_token()` 호출
- `Access Token` 저장
- 이후 REST API 호출에 Bearer 인증 사용

### 8.2 시세 조회

국내/해외 시세 API를 호출하면 현재가, 호가, 차트, 투자자 동향 등 데이터를 확인할 수 있습니다.

### 8.3 실시간 데이터 구독

WebSocket 연결 후 `get_websocket_key()`를 통해 접근 키를 발급받고, 해당 키로 실시간 구독을 시작합니다.

---

## 9. 주의 사항

### 9.1 Rate Limit

`RestClient`는 기본적으로 요청 간 1초 간격을 보장합니다.

```python
REQUEST_INTERVAL = 1.0
```

이 값은 API 호출 제한을 피하기 위한 보수적 설정이며, 필요 시 조정할 수 있습니다.

### 9.2 SSL / 폐쇄망 대응

프로젝트는 `truststore`를 사용하여 OS 인증서 저장소를 활용합니다.

- Windows: Windows 인증서 저장소
- Linux: 시스템 CA 파일
- macOS: Keychain

이를 통해 내부 CA가 설치된 폐쇄망 환경에서도 `verify=False` 방식을 피하고 안전한 운영을 유지할 수 있습니다.

---

## 10. 개발 팁

- `config.yaml.template`을 기준으로 비밀정보를 관리하세요.
- 실제 앱 키/시크릿은 커밋하지 않는 것을 권장합니다.
- 로그 파일은 `logs/` 하위에 저장됩니다.
- Docker 환경에서는 `APP_KEY`, `APP_SECRET`, `ENVIRONMENT`, `ACCOUNT_TYPE`을 환경변수로 전달하면 편리합니다.

---
