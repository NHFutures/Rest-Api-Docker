# NH선물 REST API 파이썬 애플리케이션 Docker 이미지
# 사용법: docker build -t nh-open-api .
#        docker run -it --env APP_KEY=xxx --env APP_SECRET=xxx nh-open-api

FROM python:3.14-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치 (캐시 레이어 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p logs

# 환경변수 기본값 설정
# Docker 실행 시 -e 옵션으로 오버라이드 가능
ENV APP_KEY=""
ENV APP_SECRET=""
ENV ENVIRONMENT="demo"
ENV ACCOUNT_TYPE="domestic"

# 터미널 인터랙티브 모드로 실행
# Entrypoint: render_config.py를 먼저 실행하여 config.ymal 파일 생성
# 이후 기존 CMD 명령어 실행 (기본값: python -u main.py)
ENTRYPOINT ["python", "/app/render_config.py"]
CMD ["python", "-u", "main.py"]
