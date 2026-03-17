# SecToolkit
보안팀 폐쇄망용 분석 도구 패키지

## 1. 개요
보안 운영 및 분석 업무를 위한 데이터 변환 및 네트워크 분석 유틸리티 모음입니다. 폐쇄망 환경에서 CDN이나 외부 API 없이 독립적으로 동작하는 것을 목표로 합니다.

## 2. 주요 기능
- **Multi-Decoder:** URL 및 Base64 디코딩 (Hex, HTML Entity 확장 가능)
- **Byte Counter:** 텍스트 인코딩별 바이트 크기 계산 (UTF-8, EUC-KR)
- **Network Unit Converter:** Mbps ↔ MB/s 변환
- **JSON Beautifier:** 로그 분석용 정렬 및 문법 강조
- **HAR Header Extractor:** HAR 파일 파싱 및 주요 헤더 추출

## 3. 시작하기
```bash
# 가상환경 생성 및 실행
python -m venv venv
source venv/bin/activate  # Mac/Linux

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload
```
